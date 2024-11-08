# Custom Container Images

Most of these images consist only of or include  manipulating the UID/GID of the running process within the container.

Because we volume mount data directories in most of these images, we want to ensure the UID/GID ownership allows the host user to manipulate the files as well. To do this, we need to ensure those UID/GIDs also exist in the image OS and have ownership. Because the host user's exact UID/GIDs depends on the running environment, we supply these vals via docker build args and create the necessary UID/GID in the `Dockerfile`.

Other images consist of the traditional "add our own startup scripts/configs" type images.

To understand what each image does, check the base image's documentation. Eg, `itzg/minecraft-server` can be found at [https://hub.docker.com/r/itzg/minecraft-server/](https://hub.docker.com/r/itzg/minecraft-server/) and `nginxproxy/nginx-proxy` can be found at [https://hub.docker.com/r/nginxproxy/nginx-proxy](https://hub.docker.com/r/nginxproxy/nginx-proxy).