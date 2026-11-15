FROM frappe/bench:latest

USER frappe

RUN pyenv install -s 3.12.15

ENV PYENV_VERSION=3.12.15
ENV PATH="/home/frappe/.pyenv/versions/3.12.15/bin:${PATH}"

WORKDIR /home/frappe