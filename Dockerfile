FROM ruby:3.4-slim
LABEL maintainer="h3ct0r"

# Build tools for native gems, ImageMagick for jekyll-imagemagick, Node.js as the JS runtime for jekyll-minifier
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential git imagemagick nodejs \
    && rm -rf /var/lib/apt/lists/*

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
WORKDIR /srv/jekyll
COPY Gemfile Gemfile.lock /srv/jekyll/
RUN bundle install

EXPOSE 8080
CMD ["bundle", "exec", "jekyll", "serve", "--watch", "--port=8080", "--host=0.0.0.0"]
