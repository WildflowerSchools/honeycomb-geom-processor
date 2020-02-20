import logging
import numpy as np
import psycopg2
from psycopg2 import extras

import honeycomb_tools.handle_extensions
from honeycomb_tools.handle_utils import IteratorFile

SAMPLES_INSERT = """
    INSERT INTO samples
        (status, start_time, end_time, frames_per_second, num_frames, frame_width, frame_height, environment_id, source_id, source_type, source_name, inference_id, inference_name, inference_model, inference_version)
    VALUES (%(status)s, %(start_time)s, %(end_time)s, %(frames_per_second)s, %(num_frames)s, %(frame_width)s, %(frame_height)s, %(environment_id)s, %(source_id)s, %(source_type)s, %(source_name)s, %(inference_id)s, %(inference_name)s, %(inference_model)s, %(inference_version)s)
    RETURNING id
"""

SAMPLES_UPDATE_STATUS = """
    UPDATE samples SET status = %(status)s WHERE id = %(sample_id)s
"""

SAMPLES_DELETE = """
    DELETE FROM samples WHERE id = %(sample_id)s
"""

GEOMS_INSERT = """
    INSERT INTO geoms
        (uuid, sample_id, attributes, type, object_id, object_type, object_name)
    VALUES (%(uuid)s, %(sample_id)s, %(attributes)s, %(type)s, %(object_id)s, %(object_type)s, %(object_name)s)
    RETURNING id
"""

COORDINATES_INSERT = """
    INSERT INTO coordinates
        (device_id, assignment_id, geom_id, time, coordinates)
    VALUES (%(device_id)s, %(assignment_id)s, %(geom_id)s, %(time)s, %(coordinates)s)
    RETURNING id
"""

COORDINATES_INSERT_MANY = """
    INSERT INTO coordinates
        (geom_id, device_id, assignment_id time, coordinates)
    VALUES %s
"""


def put_sample(cursor, status, start_time, end_time, frames_per_second, num_frames, frame_width, frame_height, environment_id, source_id, source_type, source_name, inference_id=None, inference_name=None, inference_model=None, inference_version=None):
    """
    Insert sample record into database and return record ID

    :param cursor - DB Transaction
    :param status -- string
    :param start_time -- date
    :param end_time -- date
    :param frames_per_second -- int
    :param num_frames -- int
    :param frame_width -- int
    :param frame_height -- int
    :param source_id -- string
    :param source_type -- string
    :param source_name -- string
    :param inference_id -- string
    :param inference_name -- string
    :param inference_model -- string
    :param inference_version -- string
    :return sample id -- int
    """
    sample_id = None
    try:
        cursor.execute(SAMPLES_INSERT, {
            'status': status,
            'start_time': start_time,
            'end_time': end_time,
            'frames_per_second': frames_per_second,
            'num_frames': num_frames,
            'frame_width': frame_width,
            'frame_height': frame_height,
            'environment_id': environment_id,
            'source_id': source_id,
            'source_type': source_type,
            'source_name': source_name,
            'inference_id': inference_id,
            'inference_name': inference_name,
            'inference_model': inference_model,
            'inference_version': inference_version
        })

        sample_id = cursor.fetchone()[0]
    except (Exception, psycopg2.DatabaseError):
        logging.exception("Failed to insert Sample record")

    return sample_id


def update_sample_status(cursor, sample_id, status):
    try:
        cursor.execute(SAMPLES_UPDATE_STATUS, {
                       'sample_id': sample_id,
                       'status': status
        })
    except (Exception, psycopg2.DatabaseError):
        logging.exception("Failed to update Sample record")
        return False

    return True


def delete_sample(cursor, sample_id):
    try:
        cursor.execute(SAMPLES_DELETE, {
            'sample_id': sample_id
        })
    except (Exception, psycopg2.DatabaseError):
        logging.exception("Failed to delete Sample record")
        return False

    return True


def put_geom(cursor, uuid, sample_id, attributes, geom_type, object_id, object_type, object_name):
    """
    Insert geom record into database and return record ID

    Keyword arguments:
    :param cursor - DB Transaction
    :param uuid -- string
    :param sample_id -- int
    :param attributes -- JSON
    :param geom_type -- string
    :param object_id -- string
    :param object_type -- string
    :param object_name -- string
    :return geom id -- int
    """
    geom_id = None
    try:
        cursor.execute(GEOMS_INSERT, {
            'uuid': uuid,
            'sample_id': sample_id,
            'attributes': attributes,
            'type': geom_type,
            'object_id': object_id,
            'object_type': object_type,
            'object_name': object_name
        })
        geom_id = cursor.fetchone()[0]
    except (Exception, psycopg2.DatabaseError):
        logging.exception("Failed to insert Geom record")

    return geom_id


def put_coordinate(cursor, device_id, assignment_id, geom_id, time, coordinates):
    """
    Insert coordinate record into database and return record ID

    :param cursor DB Transaction
    :param assignment_id - int
    :param device_id -- int
    :param geom_id -- int
    :param time -- date
    :param coordinates -- [float]
    :return record id -- int
    """
    coordinate_id = None
    try:
        cursor.execute(COORDINATES_INSERT, {
            'device_id': device_id,
            'assignment_id': assignment_id,
            'geom_id': geom_id,
            'time': time,
            'coordinates': coordinates
        })
        coordinate_id = cursor.fetchone()[0]

    except (Exception, psycopg2.DatabaseError):
        logging.exception("Failed to insert Coordinate record")

    return coordinate_id


def put_coordinates_list(cursor, coordinates):
    """
    Insert a batch of coordinate records into database and return boolean for success/failure

    :param cursor: DB Transaction
    :param coordinates: [{'device_id': int, 'assignment_id': int, 'geom_id': int, 'time': datetime, 'coordinates': []}]
    :return success: boolean
    """
    success = False
    try:
        # Use execute_values
        # psycopg2.extras.execute_values(cursor, COORDINATES_INSERT_MANY, coordinates, "(%(sample_id)s, %(geom_id)s, %(time)s, %(coordinates)s)", 100000)

        def coordinate_generator():
            for coordinate in coordinates:
                clean_coordinates = np.where(np.isnan(coordinate['coordinates']), "NULL", coordinate['coordinates'])
                str_coordinates = "{%s}" % (','.join(clean_coordinates.tolist()))
                yield "\t".join([str(coordinate['device_id']), str(coordinate['assignment_id']), str(coordinate['geom_id']), str(coordinate['time']), str_coordinates])
                #formatted_content.append("\t".join([str(coordinate['sample_id']), str(coordinate['geom_id']), str(coordinate['time']), str_coordinates]))

        f = IteratorFile(coordinate_generator())

        cursor.copy_from(f, 'coordinates', columns=('device_id', 'assignment_id', 'geom_id', 'time', 'coordinates'))

        success = True
    except (Exception, psycopg2.DatabaseError):
        logging.exception("Failed to insert collection of Coordinate records")

    return success
