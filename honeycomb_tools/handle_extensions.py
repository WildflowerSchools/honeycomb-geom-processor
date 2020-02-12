import numpy as np
import psycopg2
from psycopg2.extensions import adapt


def nan_to_null(f,
                _NULL=psycopg2.extensions.AsIs('NULL'),
                _NaN=np.NaN,
                _Float=psycopg2.extensions.Float):
    """
    Handle NaNs when inserting to Postgres

    Thanks to Gregory Arenius and piro: https://stackoverflow.com/questions/32107558/how-do-i-convert-numpy-nan-objects-to-sql-nulls

    :param f:
    :param _NULL:
    :param _NaN:
    :param _Float:
    :return:
    """
    if f is not _NaN:
        return _Float(f)
    return _NULL


def ndarray_to_pglist(a,
                      _NULL=psycopg2.extensions.AsIs('NULL'),
                      _NaN=np.NaN,
                      _Float=psycopg2.extensions.Float):

    array_with_null = np.where(np.isnan(a), _NULL, a)
    return psycopg2.extensions.AsIs("'{%s}'" % (",".join(str(v) for v in list(array_with_null))))


psycopg2.extensions.register_adapter(float, nan_to_null)
psycopg2.extensions.register_adapter(np.ndarray, ndarray_to_pglist)
