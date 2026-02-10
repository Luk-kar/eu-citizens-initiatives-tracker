FROM apache/airflow:3.0.1

USER root

# Install Chrome dependencies and Chrome
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# Install Python dependencies
COPY ECI_initiatives/data_pipeline/requirements.prod.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.prod.txt

# Note: Notebook dependencies installed in separate venvs at runtime to avoid conflicts