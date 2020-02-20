from datetime import datetime, timedelta, timezone
import logging
import os.path

import click
import honeycomb
import psycopg2
from psycopg2 import pool

import honeycomb_tools.config as config
from honeycomb_tools.process import process_geoms_2d


@click.group()
@click.pass_context
def main(ctx):
    ctx.ensure_object(dict)

    if config.HONEYCOMB_CLIENT_ID is None:
        raise ValueError("HONEYCOMB_CLIENT_ID is required")
    if config.HONEYCOMB_CLIENT_SECRET is None:
        raise ValueError("HONEYCOMB_CLIENT_SECRET is required")

    ctx.obj['honeycomb_client'] = honeycomb.HoneycombClient(
        uri=config.HONEYCOMB_URI,
        client_credentials={
            'token_uri': config.HONEYCOMB_TOKEN_URI,
            'audience': config.HONEYCOMB_AUDIENCE,
            'client_id': config.HONEYCOMB_CLIENT_ID,
            'client_secret': config.HONEYCOMB_CLIENT_SECRET,
        }
    )

    try:
        ctx.obj['pg'] = psycopg2.pool.ThreadedConnectionPool(1, 20, user=config.PG_USER,
                                                             password=config.PG_PASSWORD,
                                                             host=config.PG_HOST,
                                                             port=config.PG_PORT,
                                                             database=config.PG_DATABASE)
        conn = ctx.obj['pg'].getconn()
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        cursor.close()
        ctx.obj['pg'].putconn(conn)
    except psycopg2.OperationalError as err:
        logger.exception('Unable to establish database connection')
        raise err


@main.command()
@click.pass_context
@click.option('--environment_name', "-e", help='name of the environment in honeycomb, required for using the honeycomb consumer', required=True)
@click.option('--day', "-d", help='day expects format to be YYYY-MM-DD', required=True)
@click.option('--source', "-s", help='name of the source type to generate geoms for [''cuwb'']', required=True)
def prepare_geoms_for_environment_for_day_for_source(ctx, environment_name, day, source):
    datetime_of_day = parse_day(day)
    # prepare list of datapoints for each assignment for the time period selected
    start = (datetime_of_day + timedelta(hours=13)).isoformat()
    end = (datetime_of_day + timedelta(hours=22)).isoformat()
    ctx.invoke(prepare_geoms_for_environment_for_time_range_for_source, environment_name=environment_name, start=start, end=end, source=source)


@main.command()
@click.pass_context
@click.option('--environment_name', "-e", help='name of the environment in honeycomb, required for using the honeycomb consumer', required=True)
@click.option('--start', help='start time of video to load expects format to be YYYY-MM-DDTHH:MM', required=True)
@click.option('--end', help='end time of video to load expects format to be YYYY-MM-DDTHH:MM', required=True)
@click.option('--source', "-s", help='name of the source type to generate geoms for [''cuwb'']', required=True)
def prepare_geoms_for_environment_for_time_range_for_source(ctx, environment_name, start, end, source):
    honeycomb_client = ctx.obj['honeycomb_client']
    pg_client = ctx.obj['pg']

    start_time = parse_time(start)
    end_time = parse_time(end)

    if source == 'cuwb':
        process_geoms_2d(
            honeycomb_client=honeycomb_client,
            pg_client=pg_client,
            environment_name=environment_name,
            start_time=start_time,
            end_time=end_time,
            source_type=source)
    else:
        logger.warning('Unsupported source type: %s', source)

    if pg_client is not None:
        pg_client.closeall()


@main.command()
@click.pass_context
@click.option('--inference_id', "-i", help='inference id for generating pose geoms', required=True)
@click.option('--source', "-s", help='name of the source type to generate geoms for [''cuwb'', ''pose'']', required=True)
def prepare_geoms_for_inference_id_for_source(ctx, inference_id, source):
    honeycomb_client = ctx.obj['honeycomb_client']
    pg_client = ctx.obj['pg']

    if source == 'pose':
        process_geoms_2d(
            honeycomb_client=honeycomb_client,
            pg_client=pg_client,
            inference_id=inference_id,
            source_type=source)
    else:
        logger.warning('Unsupported source type: %s', source)

    if pg_client is not None:
        pg_client.closeall()


@main.command()
@click.pass_context
@click.option('--environment_name', "-e", help='name of the environment in honeycomb, required for using the honeycomb consumer', required=True)
@click.option('--pickle_url', "-p", help='pickle file url', required=True)
@click.option('--source', "-s", help='name of the source type to generate geoms for [''tray_detection'']', required=True)
def prepare_geoms_for_environment_for_url_for_source(ctx, environment_name, pickle_url, source):
    honeycomb_client = ctx.obj['honeycomb_client']
    pg_client = ctx.obj['pg']

    if source == 'tray_detection':
        process_geoms_2d(
            honeycomb_client=honeycomb_client,
            pg_client=pg_client,
            environment_name=environment_name,
            pickle_url=pickle_url,
            source_type=source)
    else:
        logger.warning('Unsupported source type: %s', source)

    if pg_client is not None:
        pg_client.closeall()


def parse_day(day):
    return datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def parse_time(time):
    return datetime.strptime(time, "%Y-%m-%dT%H:%M").replace(tzinfo=timezone.utc)


if __name__ == '__main__':
    logger = logging.getLogger()

    logger.setLevel(os.getenv("LOG_LEVEL", logging.INFO))
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    main(auto_envvar_prefix="HONEYCOMB")
