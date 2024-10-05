FROM itzg/mc-proxy

# Set up UID/GID
ARG HOST_UID=1000
ARG HOST_GID=1000
ENV UID=$HOST_UID
ENV GID=$HOST_GID

RUN if [ "$(cat /etc/group | grep :${GID}:)" = "" ]; then \
        groupadd --force --gid $GID mcproxy; \
    else \
        echo "Group with GID ${GID} already exists - skipping groupadd"; \
    fi


RUN if [ "$(cat /etc/passwd | grep :${UID}:)" = "" ]; then \
        useradd --uid $UID --gid $GID --shell /bin/bash --create-home mcproxy; \
    else \
        echo "User with UID ${UID} already exists - just adding GID to user"; \
        usermod -a -G $GID $(cat /etc/passwd | grep $UID | cut -d: -f1); \
    fi

RUN chown -R $UID:$GID /server