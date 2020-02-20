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

exports.up = function(db, callback) {
  async.series([
    db.addColumn.bind(db, 'samples', 'inference_id', {
      type: 'string'
    }),
    db.addColumn.bind(db, 'samples', 'inference_name', {
      type: 'string'
    }),
    db.addColumn.bind(db, 'samples', 'inference_model', {
      type: 'string'
    }),
    db.addColumn.bind(db, 'samples', 'inference_version', {
      type: 'string'
    })
  ], callback);
};

exports.down = function(db, callback) {
  async.series([
    db.removeColumn.bind(db, 'samples', 'inference_id'),
    db.removeColumn.bind(db, 'samples', 'inference_name'),
    db.removeColumn.bind(db, 'samples', 'inference_model'),
    db.removeColumn.bind(db, 'samples', 'inference_version')
  ], callback);
};

exports._meta = {
  "version": 1
};
