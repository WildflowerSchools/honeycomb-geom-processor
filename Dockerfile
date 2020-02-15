FROM node:10.18.1-alpine

WORKDIR /app

COPY package.json /app
COPY package-lock.json /app

RUN npm install --only=production

COPY .db-migraterc /app
COPY db_migrations/ /app/db_migrations
COPY scripts/ /app/scripts
COPY src/ /app/src

CMD ["scripts/setup-and-startup.sh"]