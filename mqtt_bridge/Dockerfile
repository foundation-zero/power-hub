# syntax=docker/dockerfile:1

# Comments are provided throughout this file to help you get started.
# If you need more help, visit the Dockerfile reference guide at
# https://docs.docker.com/go/dockerfile-reference/

# Want to help us make this template better? Share your feedback here: https://forms.gle/ybq9Krt8jtBL3iCk7

ARG NODE_VERSION=20.9.0
ARG PNPM_VERSION=8.15.5

FROM node:${NODE_VERSION}-alpine

# Use development for installing dev dependencies
ENV NODE_ENV development

WORKDIR /usr/src/app

# Install pnpm.
RUN --mount=type=cache,target=/root/.npm \
    npm install -g pnpm@${PNPM_VERSION}

RUN npm install typescript -g

COPY package.json .
RUN pnpm install

# Copy the rest of the source files into the image.
COPY . .
COPY .env .

# Generate js files from typescript
RUN tsc

ENV NODE_ENV production

# Run the application.
CMD ["node", "dist/serve.mjs"]
