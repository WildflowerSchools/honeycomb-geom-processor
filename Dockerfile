FROM node:10.18.1-alpine

WORKDIR /app

COPY package.json /app
COPY package-lock.json /app

RUN npm install --only=production

COPY src/ /app/

CMD ["scripts/setup-and-startup.sh"]