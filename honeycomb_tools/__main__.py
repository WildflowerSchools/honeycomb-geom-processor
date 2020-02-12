from datetime import datetime, timedelta, timezone
import logging
import os.path

import click
from dotenv import load_dotenv
import honeycomb
import psycopg2
from psycopg2 import pool

from honeycomb_tools.process import process_geoms_2d

load_dotenv()

HONEYCOMB_URI = os.getenv("HONEYCOMB_URI", "https://honeycomb.api.wildflower-tech.org/graphql")
HONEYCOMB_TOKEN_URI = os.getenv("HONEYCOMB_TOKEN_URI", "https://wildflowerschools.auth0.com/oauth/token")
HONEYCOMB_AUDIENCE = os.getenv("HONEYCOMB_AUDIENCE", "https://honeycomb.api.wildflowerschools.org")
HONEYCOMB_CLIENT_ID = os.getenv("HONEYCOMB_CLIENT_ID")
HONEYCOMB_CLIENT_SECRET = os.getenv("HONEYCOMB_CLIENT_SECRET")

PG_USER = os.getenv("PGUSER", "geom-processor")
PG_PASSWORD = os.getenv("PGPASSWORD", "iamaninsecurepassword")
PG_DATABASE = os.getenv("PGDATABASE", "geom-processor")
PG_PORT = os.getenv("PGPORT", "5432")
PG_HOST = os.getenv("PGHOST", "localhost")

@click.group()
@click.pass_context
def main(ctx):
    ctx.ensure_object(dict)

    if HONEYCOMB_CLIENT_ID is None:
        raise ValueError("HONEYCOMB_CLIENT_ID is required")
    if HONEYCOMB_CLIENT_SECRET is None:
        raise ValueError("HONEYCOMB_CLIENT_SECRET is required")

    ctx.obj['honeycomb_client'] = honeycomb.HoneycombClient(
        uri=HONEYCOMB_URI,
        client_credentials={
            'token_uri': HONEYCOMB_TOKEN_URI,
            'audience': HONEYCOMB_AUDIENCE,
            'client_id': HONEYCOMB_CLIENT_ID,
            'client_secret': HONEYCOMB_CLIENT_SECRET,
        }
    )

    try:
        ctx.obj['pg'] = psycopg2.pool.ThreadedConnectionPool(1, 20, user=PG_USER,
                                                             password=PG_PASSWORD,
                                                             host=PG_HOST,
                                                             port=PG_PORT,
                                                             database=PG_DATABASE)
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
@click.option('--source', "-s", help='name of the source type to generate geoms for [''cuwb'', ''poseflow'', ''alphapose'']', required=True)
def prepare_geoms_for_environment_for_day_for_source(ctx, environment_name, day, source):
    datetime_of_day = parse_day(day)
    # prepare list of datapoints for each assignment for the time period selected
    start = (datetime_of_day + timedelta(hours=13)).isoformat()
    end = (datetime_of_day + timedelta(hours=22)).isoformat()
    ctx.invoke(prepare_geoms_for_environment_for_time_range, environment_name=environment_name, start=start, end=end, source=source)


@main.command()
@click.pass_context
@click.option('--environment_name', "-e", help='name of the environment in honeycomb, required for using the honeycomb consumer', required=True)
@click.option('--start', help='start time of video to load expects format to be YYYY-MM-DDTHH:MM', required=True)
@click.option('--end', help='end time of video to load expects format to be YYYY-MM-DDTHH:MM', required=True)
@click.option('--source', "-s", help='name of the source type to generate geoms for [''cuwb'', ''poseflow'', ''alphapose'']', required=True)
def prepare_geoms_for_environment_for_time_range(ctx, environment_name, start, end, source):
    honeycomb_client = ctx.obj['honeycomb_client']
    pg_client = ctx.obj['pg']

    start_time = parse_time(start)
    end_time = parse_time(end)

    if source == 'cuwb':
        process_geoms_2d(honeycomb_client, pg_client, environment_name, start_time, end_time)

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
