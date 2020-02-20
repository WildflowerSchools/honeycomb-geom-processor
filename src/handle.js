const { Pool } = require("pg")
const pool = new Pool()

exports.fetchSample = async function(environmentId, date) {
  try {
    const sql = `
      WITH max_sample_id AS (
        SELECT MAX(id) as id
        FROM samples
        WHERE
          environment_id = '${environmentId}'
          AND start_time::date = '${date}'::date
          AND status = 'success'
      )
      SELECT
        s.id,
        s.start_time,
        s.end_time,
        s.frames_per_second,
        s.num_frames,
        s.frame_width,
        s.frame_height,
        s.source_type,
        s.source_name
      FROM
        samples s
        JOIN max_sample_id m ON s.id = m.id`

    const { rows } = await pool.query(sql)
    return rows[0]
  } catch (e) {
    console.error("Handle - fetchSample failed")
    throw e
  }
}

exports.fetchGeomsForSample = async function(sample_id) {
  try {
    const sql = `
      SELECT
        g.id,
        g.attributes,
        g.type,
        g.object_id,
        g.object_type,
        g.object_name
      FROM
        geoms g
      WHERE
        g.sample_id = '${sample_id}'`

    const { rows } = await pool.query(sql)
    return rows
  } catch (e) {
    console.error("Handle - fetchGeoms failed")
    throw e
  }
}

exports.fetchCoordinatesForSampleAndDeviceWithTime = async function(
  sample_id,
  device_id,
  from,
  seconds
) {
  try {
    const sql = `
      WITH inputs AS (
        SELECT
          ${sample_id} as sample_id,
          '${device_id}' as device_id,
          '${from}'::TIMESTAMP as from,
          ('${from}'::TIMESTAMP + interval '${seconds} seconds') as to
      )
      SELECT
        c.geom_id,
        EXTRACT(epoch FROM c.time) * 1000 as time,
        c.coordinates
      FROM
        inputs,
        coordinates c JOIN geoms g ON c.geom_id = g.id
      WHERE
        g.sample_id = inputs.sample_id
        AND c.device_id = inputs.device_id
        AND c.time BETWEEN inputs.from AND inputs.to
      ORDER BY
        c.geom_id, c.time ASC`

    const { rows } = await pool.query(sql)
    return rows
  } catch (e) {
    console.error("Handle - fetchCoordinatesForSampleAndDeviceWithTime failed")
    throw e
  }
}

exports.fetchCoordinatesForGeomAndDeviceWithTime = async function(
  geom_id,
  device_id,
  from,
  seconds = 25
) {
  try {
    const sql = `
      WITH inputs AS (
        SELECT
          ${geom_id} as geom_id,
          ${device_id} as device_id,
          ${from}::TIMESTAMP as from,
          (${from}::TIMESTAMP + interval '${seconds} seconds') as to
      )
      SELECT
        c.geom_id,
        EXTRACT(epoch FROM c.time) * 1000,
        c.coordinates
      FROM
        time_inputs,
        coordinates c
      WHERE
        c.device_id = inputs.device_id
        AND c.time BETWEEN inputs.from AND inputs.to
        AND c.geom_id = inputs.geom_id
      ORDER BY
        c.time ASC`

    const { rows } = await pool.query(sql)
    return rows
  } catch (e) {
    console.error("Handle - fetchCoordinatesForGeomAndDeviceWithTime failed")
    throw e
  }
}
