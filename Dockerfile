
# Get a distribution that has uv already installed
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# Add user - this is the user that will run the app
# If you do not set user, the app will run as root (undesirable)
RUN useradd -m -u 1000 user
USER user

# Set the home directory and path
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH        

ENV UVICORN_WS_PROTOCOL=websockets


# Set the working directory
WORKDIR $HOME/app

COPY --chown=user ./pyproject.toml $HOME/app
COPY --chown=user ./uv.lock $HOME/app

# Install the dependencies
# RUN uv sync --frozen
RUN uv sync

# Copy the app to the container
COPY --chown=user ./py-src/ $HOME/app
COPY --chown=user ./.chainlit/ $HOME/app
COPY --chown=user ./chainlit.md $HOME/app

#TODO: Fix this to download 
#copy posts to container
COPY --chown=user ./data/ $HOME/app/data

# Expose the port
EXPOSE 7860

# Run the app
CMD ["uv", "run", "chainlit", "run", "app.py", "--host", "0.0.0.0", "--port", "7860"]