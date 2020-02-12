FROM node:10.17.0-alpine

WORKDIR /app

COPY package.json /app
COPY package-lock.json /app

RUN npm install --only=production

COPY src/ /app/

CMD node index.js