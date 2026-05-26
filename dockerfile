FROM registry.access.redhat.com/ubi9/ubi-minimal:9.8-1779809423 as builder
USER root
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
COPY pyproject.toml .
COPY uv.lock .
RUN microdnf install --setopt=install_weak_deps=0 --nodocs -y python3.12 tar gzip && \
    /bin/curl -LsSf https://astral.sh/uv/0.11.16/install.sh | sh && \
    microdnf clean all
ENV PATH="root/.local/bin/env:/usr/app/venv/bin:$PATH"
RUN bash -c "source $HOME/.local/bin/env && \
    uv venv --link-mode clone --seed /usr/app/venv && \
    source usr/app/venv/bin/activate && \
    uv sync --active --no-dev --frozen --no-install-project --no-editable"

LABEL maintainer="Joe Targett"

FROM registry.access.redhat.com/ubi9/ubi-minimal:9.8-1779809423 as prod
# RUN useradd -ms /bin/bash app
COPY --from=builder /usr/app/venv /usr/app/venv
COPY --from=builder /root/.local/share/uv/python /root/.local/share/uv/python
# USER app
COPY . /usr/app
EXPOSE 8080
WORKDIR /usr/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV VIRTUAL_ENV=/usr/app/venv
ENV PATH="/usr/app/venv/bin:$PATH"
CMD ["bash", "-c", "source /usr/app/venv/bin/activate && /usr/app/venv/bin/python3.14 -m main"]