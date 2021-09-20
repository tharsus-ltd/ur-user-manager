FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8

# Install requirements
COPY ./requirements.txt /tmp/pip-tmp/requirements.txt
RUN pip3 --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements.txt && rm -rf /tmp/pip-tmp

# Add source code and set working directory
ADD ./app /app/app
WORKDIR /app
