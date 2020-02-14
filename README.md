# honeycomb-geom-processor

Processes and loads geom data into a timeseriesDB. Geoms are made available over a websocket API.

Daemon services include a Node server hosting the socket API and a TimeScaleDB database for storage. The honeycomb_tools directory includes a python app for generating geom data and staging into the timeseries database.

## Node Socket API

API is available via `https://<<HOST>>:<<PORT>>/ws`

#### Connect and Authenticate:

1) Establish Websocket Connection

2) Authenticate

    All communication requires authentication except Connect and Ping/Pong
    
    Client Message:
    ```
        {
            "auth", {
                "Authorization": "<<BEARER_TOKEN>>>"
            }
        }
    ```
   
    Server Success Response:
    ```
        {
            "authorized", {}
        }
    ```
   
    Server Error Response:
    ```
        {
            "error", {
                "message": "Unauthorized",
                "code": 4401
            }
        }
    ```

#### Ping <-> Pong

Server expects every client to ping at least once a minute. Server will respond with a pong containing the ping's message data. Clients can use this to implement their own heartbeat.

Client Message:
```
    {
        "ping": {
            "test": "data"
        }
    }
```

Server Response:
```
    {
        "pong": {
            "test": "data"
        }
    }
```

#### Get "Sample" and Geoms:

Client will first ask for geoms. The response will send back a "sample" with meta data and a list of geoms.

Client Message:
```
    {
        "getGeoms": {
            "environment_id": "<<ENVIRONMENT_ID",
            "date": "<<YYYY-MM-DD>>"
        }
    }
```

Server Response:
```
    {
        "geoms": {
            "sample": {},
            "geoms": [
                {
                }
            ]
        }
    }
```

#### Get Coordinates:

Client can use the sampleID to request coordinates. 25 seconds of coordinates are returned keyed by geom_id and epoch time

Client Message:
```
    {
        "getCoordinates": {
            "sample_id": "<<SAMPLE_ID>>",
            "device_id": "<<DEVICE_ID>>",
            "from": "<<YYYY-MM-DDThh:mm:ss>>"
        }
    }
```

Server Response:
```
    {
        "coordinates": {
            "<<GEOM_ID>>": {
                "<<EPOCH_TIME>>": [<<COORDINATES>>]
            }
        }
    }
```

## Development

`docker-compose build && docker-compose up`

Open: [https://localhost:8010](https://localhost:8010)

### Prepare Geoms

**NOTE:**

Prepare can use a lot of memory (> 2GB for a full day of CUWB). If you haven't committed that much memory to your docker environment, it may be better to run 'prepare' locally.

*RUN (Docker):*

```
docker-compose run -e START_TIME=<<YYYY-MM-DDThh:mm>> -e END_TIME=<<YYYY-MM-DDThh:mm>> -e SOURCE=cuwb -e ENVIRONMENT_NAME=<<environment>> --entrypoint 'sh' geom-processor-prepare '/app/prepare-geoms.sh'
```

*RUN (Locally):*

1) Build:

    `python setup.py build && python setup.py install`

2) Execute

    Edit justfile vars and use: `just prep-geoms`
    
    Or: 
    ```
    python -m honeycomb_tools prepare-geoms-for-environment-for-time-range-for-source --environment_name {{environment_name}} --start {{start}} --end {{end}} --source {{source}}
    ```
