# honeycomb-geom-processor

## Development

`docker-compose build && docker-compose up`

Open: [https://localhost:8010](https://localhost:8010)

### Prepare Geoms

*BUILD:*

```docker build -t honeycomb-geom-processor:prepare -f Prepare.Dockerfile .```

*RUN:*

```docker run --env-file ./honeycomb_tools/.env --network honeycomb-geom-processor_default honeycomb-geom-processor:prepare```
