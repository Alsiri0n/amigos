FROM python:bullseye
RUN useradd amigos
RUN mkdir -p /usr/src/app/amigos
WORKDIR /usr/src/app/amigos
COPY requirements.txt ./
RUN pip install --no-cache-dir -r ./requirements.txt
COPY . /usr/src/app/amigos/
RUN chmod +x /usr/src/app/amigos/boot.sh
ENTRYPOINT ["./boot.sh"]
EXPOSE 8080