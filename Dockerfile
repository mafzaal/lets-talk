FROM langchain/langgraph-api:3.13-wolfi

# Install timezone data for proper timezone handling
RUN apk add --no-cache tzdata

# -- Adding local package . --
ADD . /deps/lets-talk
# -- End of local package . --

# -- Installing all local dependencies --
RUN PYTHONDONTWRITEBYTECODE=1 uv pip install --system --no-cache-dir -c /api/constraints.txt -e /deps/*
# -- End of local dependencies install --
ENV LANGGRAPH_HTTP='{"app": "/deps/lets-talk/backend/lets_talk/main.py:app"}'
ENV LANGSERVE_GRAPHS='{"react_agent": "/deps/lets-talk/backend/lets_talk/main.py:react_agent", "rag_agent": "/deps/lets-talk/backend/lets_talk/main.py:rag_agent"}'



# -- Ensure user deps didn't inadvertently overwrite langgraph-api
RUN mkdir -p /api/langgraph_api /api/langgraph_runtime /api/langgraph_license &&     touch /api/langgraph_api/__init__.py /api/langgraph_runtime/__init__.py /api/langgraph_license/__init__.py
RUN PYTHONDONTWRITEBYTECODE=1 uv pip install --system --no-cache-dir --no-deps -e /api
# -- End of ensuring user deps didn't inadvertently overwrite langgraph-api --
# -- Removing pip from the final image ~<:===~~~ --
RUN pip uninstall -y pip setuptools wheel &&     rm -rf /usr/local/lib/python*/site-packages/pip* /usr/local/lib/python*/site-packages/setuptools* /usr/local/lib/python*/site-packages/wheel* &&     find /usr/local/bin -name "pip*" -delete || true
# pip removal for wolfi
RUN rm -rf /usr/lib/python*/site-packages/pip* /usr/lib/python*/site-packages/setuptools* /usr/lib/python*/site-packages/wheel* &&     find /usr/bin -name "pip*" -delete || true
RUN uv pip uninstall --system pip setuptools wheel && rm /usr/bin/uv /usr/bin/uvx
# -- End of pip removal --

WORKDIR /deps/lets-talk


# Make entrypoint executable
RUN chmod +x /deps/lets-talk/entrypoint.sh

# Set our custom entrypoint
ENTRYPOINT ["/deps/lets-talk/entrypoint.sh"]