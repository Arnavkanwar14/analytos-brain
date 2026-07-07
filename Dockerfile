FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /root/analytos-brain

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates bash && \
    rm -rf /var/lib/apt/lists/*

# Omnigraph CLI + server binaries
RUN curl -fsSL https://raw.githubusercontent.com/ModernRelay/omnigraph/main/scripts/install.sh | bash
ENV PATH="/root/.local/bin:${PATH}"

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY . /root/analytos-brain

RUN chmod +x /root/analytos-brain/hf/start.sh

EXPOSE 7860
CMD ["/root/analytos-brain/hf/start.sh"]
