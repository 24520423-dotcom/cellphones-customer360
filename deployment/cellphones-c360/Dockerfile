ARG C360_BENCH_IMAGE=frappe/bench@sha256:0b7b1602cd7295666a260dcd2838903bed5a1b97bc003690a04c803189e1e4b4
FROM ${C360_BENCH_IMAGE}

USER frappe

RUN pyenv install -s 3.12.15

ENV PYENV_VERSION=3.12.15
ENV PATH="/home/frappe/.pyenv/versions/3.12.15/bin:${PATH}"

WORKDIR /home/frappe

RUN printf '[client]\nskip-ssl\n' > /home/frappe/.my.cnf \
    && chmod 600 /home/frappe/.my.cnf
