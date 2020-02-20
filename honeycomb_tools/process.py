from concurrent.futures import ThreadPoolExecutor, wait, FIRST_EXCEPTION
import copy
import datetime
import json
import logging
from operator import itemgetter
import os
import pickle
import psycopg2
import time

from process_cuwb_data import fetch_geoms_2d as fetch_cuwb_geoms_2d
from process_pose_data import fetch_geoms_2d_by_inference_execution as fetch_pose_geoms_2d
import geom_render
from geom_render import GeomJSONEncoder

import honeycomb_tools.config as config
from honeycomb_tools.introspection import get_device_to_assignment_mapping_at_time, get_environment_id, get_environment_for_inference_id, fetch_inference_for_inference_id
from honeycomb_tools.handle import put_sample, update_sample_status, delete_sample, put_geom, put_coordinates_list
from honeycomb_tools.util import kill_child_processes, download_pickle


#  Max number of threads = MAX_WORKERS
#  Caution, each thread will attempt to throw a large # of coordinates at postgres using the PG copy_from functionality


DEFAULT_FRAME_WIDTH = 1296
DEFAULT_FRAME_HEIGHT = 972


class ProcessingError(Exception):
    pass


def process_geoms_2d(
        honeycomb_client,
        pg_client,
        source_type,
        environment_name=None,
        start_time=None,
        end_time=None,
        inference_id=None,
        pickle_url=None):

    time_start_processing = time.perf_counter()

    inference_name, inference_model, inference_version = None, None, None

    # Load geoms
    if pickle_url is not None:
        environment_id = get_environment_id(honeycomb_client, environment_name)

        sample_collection = pickle.load(download_pickle(pickle_url))
    elif source_type == 'cuwb':
        environment_id = get_environment_id(honeycomb_client, environment_name)

        sample_collection = fetch_cuwb_geoms_2d(environment_name, start_time, end_time)
    elif source_type == 'pose':
        if inference_id is None:
            logging.warning("Source type 'pose' requires inference_id")
            return None

        inference = fetch_inference_for_inference_id(honeycomb_client, inference_id)
        if inference is None:
            logging.warning("Unable to find inference with inference id %s", inference_id)
            return None

        inference_name, inference_model, inference_version = itemgetter('inference_name', 'inference_model', 'inference_version')(inference)

        meta = get_environment_for_inference_id(honeycomb_client, inference_id)
        if meta is None:
            logging.warning("Unable to extract environment from inference id %s", inference_id)
            return None

        environment_id, environment_name = itemgetter('environment_id', 'environment_name')(meta)
        if environment_id is None or environment_name is None:
            logging.warning("Unable to extract environment from inference id: %s", meta)
            return None

        sample_collection = fetch_pose_geoms_2d(inference_id)
    else:
        logging.warning("Invalid source type: %s", source_type)
        return None

    time_fetched_sample = time.perf_counter()

    if len(sample_collection) == 0:
        logging.warning("No devices found for: Environment - %s, Start - %s, End - %s", environment_name, start_time, end_time)
        return None

    sample_collection = {k: (v['geom'] if isinstance(v, dict) else v) for k, v in sample_collection.items()}

    for _, device in sample_collection.items():
        if not isinstance(device, geom_render.core.GeomCollection2D):
            raise ProcessingError("Unexpected device type returned by geom generator, expectected GeomCollection2D, received: %s", type(device))

    # Pick a geom at random to gather some general meta information that SHOULD be common across geoms
    geom_collection_meta = next(iter(sample_collection.values()))

    if start_time is None:
        start_time = geom_collection_meta.start_time
    if end_time is None:
        end_time = geom_collection_meta.start_time + datetime.timedelta(seconds=(geom_collection_meta.num_frames / geom_collection_meta.frames_per_second))

    device_to_assignment_map = get_device_to_assignment_mapping_at_time(honeycomb_client, environment_id, start_time)

    conn = pg_client.getconn()
    cursor = conn.cursor()

    sample_db_id = None
    pool = ThreadPoolExecutor(max_workers=config.MAX_WORKERS)
    try:
        logging.info("Loading Sample (%s, %s, %s, inference_name=%s) into database...", environment_name, start_time, end_time, inference_name)
        sample_db_id = put_sample(cursor,
                                  status='started',
                                  start_time=start_time,
                                  end_time=end_time,
                                  frames_per_second=geom_collection_meta.frames_per_second,
                                  num_frames=geom_collection_meta.num_frames,
                                  frame_width=geom_collection_meta.frame_width or DEFAULT_FRAME_WIDTH,
                                  frame_height=geom_collection_meta.frame_height or DEFAULT_FRAME_HEIGHT,
                                  environment_id=environment_id,
                                  source_id=geom_collection_meta.source_id,
                                  source_type=geom_collection_meta.source_type or source_type,
                                  source_name=geom_collection_meta.source_name,
                                  inference_id=inference_id,
                                  inference_name=inference_name,
                                  inference_model=inference_model,
                                  inference_version=inference_version)

        if sample_db_id is None:
            raise ProcessingError("Failed creating sample record for %s, %s, %s, inference_name=%s" % (environment_name, start_time, end_time, inference_name))

        logging.info("Sample record staged with id %s", sample_db_id)

        # Geoms will use an autogenerated primary ID in Postgres, use this dict to build a geom uuid -> PG ID map
        geom_id_to_geom_db_id_map = dict()

        # Insert geom objects into DB
        for device_id, device in sample_collection.items():
            for geom in device.geom_list:
                if geom.id in geom_id_to_geom_db_id_map:
                    continue

                logging.info("SampleId - %s: Loading Geom (%s, %s, %s, %s) into database...", sample_db_id, type(geom).__name__, geom.object_id, geom.object_type, geom.object_name)
                geom_db_id = put_geom(cursor,
                                      uuid=geom.id,
                                      sample_id=sample_db_id,
                                      attributes=json.dumps(scrub_geom_object(geom), cls=GeomJSONEncoder),
                                      geom_type=type(geom).__name__,
                                      object_id=geom.object_id,
                                      object_type=geom.object_type,
                                      object_name=geom.object_name)
                if geom_db_id is None:
                    raise ProcessingError("SampleId - %s: Failed creating Geom record" % (sample_db_id))

                logging.info("SampleId - %s: Geom record staged with id %s", sample_db_id, geom_db_id)
                geom_id_to_geom_db_id_map[geom.id] = geom_db_id

        conn.commit()

        # Create parallel jobs to load each device's massive coordinate list into DB
        # pool_coord_insert = ThreadPoolExecutor(len(sample_collection.items()))
        futures_coord_insert = []
        for device_id, device in sample_collection.items():
            assignment_id = device_to_assignment_map[device_id]

            # Generate geoms object coordinates for each device over a separate thread
            future_prepare_coords = []
            all_coordinates = []
            for geom in device.geom_list:
                future_prepare_coords.append(pool.submit(prepare_geom_coordinates,
                                             device_id=device_id,
                                             device=device,
                                             assignment_id=assignment_id,
                                             geom=geom,
                                             geom_db_id=geom_id_to_geom_db_id_map[geom.id]))

            done, _ = wait(future_prepare_coords)
            [all_coordinates.extend(f.result()) for f in done]

            futures_coord_insert.append(pool.submit(
                pooled_put_coordinates_list,
                pg_client=pg_client,
                sample_db_id=sample_db_id,
                device_id=device_id,
                assignment_id=assignment_id,
                all_coordinates=all_coordinates))

        done, _ = wait(futures_coord_insert, return_when=FIRST_EXCEPTION)
        [f.result() for f in done]  # Raise exception if there is one

        update_sample_status(cursor, sample_db_id, 'success')
        conn.commit()

        time_loaded_sample = time.perf_counter()
        logging.info("SampleId - %s loaded! Fetch geoms time - %0.4f, Load db time %0.4f, Total time %0.4f", sample_db_id, time_fetched_sample - time_start_processing, time_loaded_sample - time_fetched_sample, time_loaded_sample - time_start_processing)

    except (Exception, psycopg2.DatabaseError, ProcessingError) as error:
        if cursor and conn and sample_db_id:
            conn.rollback()

            delete_sample(cursor, sample_db_id)
            conn.commit()

            logging.info("Cleanup, SampleId - %s deleted!", sample_db_id)
            logging.exception(error)

        if pool:
            pool.shutdown(wait=False)
            kill_child_processes(os.getpid())
            exit(1)

        raise error
    finally:
        if cursor:
            cursor.close()
        if conn:
            pg_client.putconn(conn)


def pooled_put_coordinates_list(pg_client, sample_db_id, device_id, assignment_id, all_coordinates):
    conn = pg_client.getconn()
    cursor = conn.cursor()
    try:
        time_copy_from_started = time.perf_counter()
        logging.info("SampleId - %s, DeviceId - %s, AssignmentId - %s: Loading %s coordinates into database...", sample_db_id, device_id, assignment_id, len(all_coordinates))
        success = put_coordinates_list(cursor, all_coordinates)
        if not success:
            raise ProcessingError("SampleId - %s, DeviceId - %s, AssignmentId - %s: Failed loading coordinate records" % (sample_db_id, device_id, assignment_id))

        time_copy_from_finished = time.perf_counter()
        logging.info("SampleId - %s, DeviceId - %s, AssignmentId - %s: Coordinates staged, Staging time - %0.4f", sample_db_id, device_id, assignment_id, time_copy_from_finished - time_copy_from_started)

        conn.commit()
    except (Exception, ProcessingError) as error:
        conn.rollback()

        logging.exception("SampleId - %s, DeviceId - %s, AssignmentId - %s: Failed loading coordinate records")
        raise error
    finally:
        cursor.close()
        conn.close()
        pg_client.putconn(conn)


def prepare_geom_coordinates(device_id, device, assignment_id, geom, geom_db_id):
    queued_coords = []
    ms_per_frame = 1000 / device.frames_per_second
    geom_coordinates = reshape_coordinates_using_indices(device.coordinates, geom.coordinate_indices)
    for idx, coordinates in enumerate(geom_coordinates):
        time_offset = datetime.timedelta(milliseconds=ms_per_frame * idx)
        queued_coords.append({
            'geom_id': geom_db_id,
            'device_id': device_id,
            'assignment_id': assignment_id,
            'time': device.start_time + time_offset,
            'coordinates': coordinates
        })
    return queued_coords


def scrub_geom_object(geom):
    j = copy.deepcopy(geom.__dict__)
    [j.pop(key, None) for key in ['coordinates', 'coordinate_indices', 'time_index', 'start_time', 'end_time', 'frames_per_second', 'num_frames', 'frame_width', 'frame_height']]

    if 'color' in j and j['color'] is not None and not j['color'].startswith("#"):
        j['color'] = "#{color}".format(color=j['color'])

    return j


def reshape_coordinates_using_indices(coordinates, coordinate_indices):
    """
    Reshape coordinates array into a 2D time series using coordinate_indices to extract geom's relevant points-of-interest

    Example:

    Geom Type is a 2D Line, that means two points from the coordinates array are required to draw the object

    coordinate_indices = [0, 1]

    INPUT
    [
      [
        [0, 0], # A1
        [0, 1], # A2
        [0, 2], # A3
        [0, 3]  # A4
      ],
      [
        [1, 0], # B1
        [1, 1], # B2
        [1, 2], # B3
        [1, 3], # B4
      ]
    ]

    OUTPUT (in time series compatible order)
    [
      [0, 0, 0, 1], # [...A1, ...A2]
      [1, 0, 1, 1]  # [...B1, ...B2]
    ]
    """
    return coordinates[:, coordinate_indices].reshape((-1, 2 * len(coordinate_indices)))
