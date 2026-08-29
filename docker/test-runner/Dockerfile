FROM python:3.11-slim

WORKDIR /workspace

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Ensure /tmp permissions allow user 'nobody' to write results.json
RUN chmod 777 /tmp

USER nobody

ENTRYPOINT ["pytest"]
CMD ["/workspace", "--json-report", "--json-report-file=/tmp/results.json", "-q"]
