# honeycomb-geom-rendering

## Development

`docker-compose build && docker-compose up`

Open: [https://localhost:8010](https://localhost:8010)

### Prepare Geoms

*BUILD:*

```docker build -t honeycomb-geom-rendering:prepare -f Prepare.Dockerfile .```

*RUN:*

```docker run --env-file ./honeycomb_tools/.env --network honeycomb-geom-rendering_default honeycomb-geom-rendering:prepare```
