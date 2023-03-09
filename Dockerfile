FROM python:bullseye
RUN useradd amigos
RUN mkdir -p /usr/src/app/amigos
WORKDIR /usr/src/app/amigos
# RUN python -m venv venv
COPY requirements.txt ./
# RUN venv/bin/pip install --no-cache-dir -r ./requirements.txt
RUN pip install --no-cache-dir -r ./requirements.txt
COPY . /usr/src/app/amigos/
# COPY alembic /usr/src/app/amigos/alembic
# COPY alembic.ini /usr/src/app/amigos/
# COPY config.yaml /usr/src/app/amigos/
# COPY *.py /usr/src/app/amigos/
# COPY boot.sh /usr/src/app/amigos/
# COPY .env /usr/src/app/amigos/
RUN chmod +x /usr/src/app/amigos/boot.sh
ENTRYPOINT ["./boot.sh"]
EXPOSE 8080