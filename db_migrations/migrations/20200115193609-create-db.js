'use strict';

var dbm;
var type;
var seed;

var async = require('async')

/**
 * We receive the dbmigrate dependency from dbmigrate initially.
 * This enables us to not have to rely on NODE_PATH.
 */
exports.setup = function(options, seedLink) {
  dbm = options.dbmigrate;
  type = dbm.dataType;
  seed = seedLink;
};

exports.up = function (db, callback) {
  async.series([
    db.createTable.bind(db, 'samples', {
      id: { type: 'int', primaryKey: true, autoIncrement: true },
      start_time: 'datetime',
      end_time: 'datetime',
      frames_per_second: 'int',
      num_frames: 'int',
      frame_width: 'int',
      frame_height: 'int',
      environment_id: 'string',
      source_id: 'string',
      source_type: 'string',
      source_name: 'string',
      status: 'string'
    }),
    db.createTable.bind(db, 'geoms', {
      id: { type: 'int', primaryKey: true, autoIncrement: true },
      uuid: 'string',
      attributes: 'jsonb',
      type: 'string',
      object_id: 'string',
      object_type: 'string',
      object_name: 'string',
      sample_id: {
        type: 'int',
        foreignKey: {
          name: 'geoms_sample_id_fk',
          table: 'samples',
          rules: {
            onDelete: 'CASCADE',
            onUpdate: 'RESTRICT'
          },
          mapping: {
            sample_id: 'id'
          }
        }
      }
    }),
    db.runSql.bind(db, 'CREATE UNIQUE INDEX geoms_sample_id_uuid_idx ON geoms (sample_id, uuid)'),
    db.createTable.bind(db, 'coordinates', {
      time: 'datetime',
      device_id: 'string',
      assignment_id: 'string',
      // sample_id: {
      //   type: 'int',
      //   foreignKey: {
      //     name: 'coordinates_sample_id_fk',
      //     table: 'samples',
      //     rules: {
      //       onDelete: 'CASCADE',
      //       onUpdate: 'RESTRICT'
      //     },
      //     mapping: {
      //       sample_id: 'id'
      //     }
      //   }
      // },
      geom_id: {
        type: 'int',
        foreignKey: {
          name: 'coordinates_geom_id_fk',
          table: 'geoms',
          rules: {
            onDelete: 'CASCADE',
            onUpdate: 'RESTRICT'
          },
          mapping: {
            geom_id: 'id'
          }
        }
      }
    }),
    // db.addIndex.bind(db, 'coordinates', "coordinates_sample_idx", ["sample_id"], false),
    db.addIndex.bind(db, 'coordinates', "coordinates_geom_id_idx", ["geom_id"], false),
    db.addIndex.bind(db, 'coordinates', "coordinates_device_id_idx", ["device_id"], false),
    db.addIndex.bind(db, 'coordinates', "coordinates_assignment_id_idx", ["assignment_id"], false),
    //db.runSql.bind(db, 'CREATE UNIQUE INDEX coordinates_sample_id_device_id_geom_id_time_idx ON coordinates (sample_id, device_id, geom_id, time)'),
    db.runSql.bind(db, 'CREATE UNIQUE INDEX coordinates_device_id_geom_id_time_idx ON coordinates (device_id, geom_id, time)'),
    db.runSql.bind(db, 'ALTER TABLE coordinates ADD COLUMN coordinates numeric[]'),
    db.runSql.bind(db, 'SELECT create_hypertable(\'coordinates\', \'time\')')
  ], callback);
};

exports.down = function(db, callback) {
  async.series([
    db.dropTable.bind(db, 'coordinates'),
    db.dropTable.bind(db, 'geoms'),
    db.dropTable.bind(db, 'samples')
  ], callback);
};

exports._meta = {
  "version": 1
};
