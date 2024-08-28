ARG NODE_VERSION=20
ARG PNPM_VERSION=8.15.5

FROM node:${NODE_VERSION}-alpine AS builder

# Use development for installing dev dependencies
ENV NODE_ENV development

WORKDIR /usr/src/app

# Install pnpm.
RUN --mount=type=cache,target=/root/.npm \
    npm install -g pnpm@${PNPM_VERSION}

COPY package.json .
RUN pnpm install

# Copy the rest of the source files into the image.
COPY . .

# Generate js files from typescript
RUN pnpm tsc

ENV NODE_ENV production

FROM node:${NODE_VERSION}-alpine AS release

WORKDIR /usr/src/app

COPY --from=builder /usr/src/app/node_modules node_modules
COPY --from=builder /usr/src/app/dist/ dist/

# Run the application.
CMD ["node", "dist/serve.mjs"]
