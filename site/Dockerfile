# Section 1- Base Image
FROM python:3.10-slim

# Section 2- Python Interpreter Flags
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
# Section 2.1 - Set language to english
ENV LANG en_US. UTF-8  
ENV LANGUAGE en_us:en  

# Section 3- Compiler and OS libraries
RUN apt-get update \
  && apt-get install -y --no-install-recommends build-essential libpq-dev \
  && rm -rf /var/lib/apt/lists/*

# Section 4- Project libraries and User Creation
COPY requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm -rf /tmp/requirements.txt \
    && useradd -U site \
    && install -d -m 0755 -o site -g site /site

# Section 5- Code and User Setup
WORKDIR /site
USER site:site
COPY --chown=site:site . .
#RUN chmod +x ./docker/*.sh

# Section 6- Docker Run Checks and siteurations
CMD [ "python3","main.py"]