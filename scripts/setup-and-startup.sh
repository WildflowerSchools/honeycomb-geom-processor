#!/bin/sh

npm install

npm run migrate

if [[ $? -eq 0 ]]
then
  echo "Migration ran successfully"
else
  echo "Migration failed" >&2
  exit 1
fi

npm start
