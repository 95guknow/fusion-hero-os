#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <signal.h>
#include <errno.h>
#include <arpa/inet.h>

#define IPC_SOCKET_PATH     "/tmp/fusion_hero_ipc.sock"
#define FHOS_IPC_MAGIC      0x46484F53
#define FHOS_IPC_VERSION    0x01
#define MAX_PAYLOAD_SIZE    (1024 * 1024)

#ifndef MSG_NOSIGNAL
#define MSG_NOSIGNAL 0
#endif

typedef struct __attribute__((packed, aligned(4))) {
    uint32_t magic;
    uint8_t  version;
    uint8_t  msg_type;
    uint16_t status_code;
    uint32_t payload_len;
    uint32_t reserved;
} fhos_ipc_header_t;

ssize_t recv_exact(int fd, void *buf, size_t n) {
    size_t bytes_left = n;
    ssize_t bytes_read;
    char *ptr = (char *)buf;

    while (bytes_left > 0) {
        bytes_read = recv(fd, ptr, bytes_left, 0);
        if (bytes_read < 0) {
            if (errno == EINTR) continue;
            return -1;
        } else if (bytes_read == 0) {
            break;
        }
        bytes_left -= bytes_read;
        ptr += bytes_read;
    }
    return (n - bytes_left);
}

void start_ipc_server(void) {
    int listen_fd, client_fd;
    struct sockaddr_un server_addr;

    signal(SIGPIPE, SIG_IGN);

    if ((listen_fd = socket(AF_UNIX, SOCK_STREAM, 0)) == -1) {
        perror("[FHOS-Kernel] socket() failed");
        exit(EXIT_FAILURE);
    }

    unlink(IPC_SOCKET_PATH);

    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sun_family = AF_UNIX;
    strncpy(server_addr.sun_path, IPC_SOCKET_PATH, sizeof(server_addr.sun_path) - 1);

    if (bind(listen_fd, (struct sockaddr *)&server_addr, sizeof(server_addr)) == -1) {
        perror("[FHOS-Kernel] bind() failed");
        close(listen_fd);
        exit(EXIT_FAILURE);
    }

    if (listen(listen_fd, 20) == -1) {
        perror("[FHOS-Kernel] listen() failed");
        close(listen_fd);
        exit(EXIT_FAILURE);
    }

    printf("[FHOS-Kernel] IPC Server listening on %s\n", IPC_SOCKET_PATH);

    while (1) {
        client_fd = accept(listen_fd, NULL, NULL);
        if (client_fd == -1) {
            perror("[FHOS-Kernel] accept() failed");
            continue;
        }

        printf("[FHOS-Kernel] Python client connected (fd=%d)\n", client_fd);

        fhos_ipc_header_t req_header;

        if (recv_exact(client_fd, &req_header, sizeof(req_header)) == sizeof(req_header)) {
            uint32_t magic       = ntohl(req_header.magic);
            uint32_t payload_len = ntohl(req_header.payload_len);

            if (magic == FHOS_IPC_MAGIC && req_header.version == FHOS_IPC_VERSION) {
                char *payload = NULL;
                uint16_t response_status = 0x0000;

                if (payload_len > MAX_PAYLOAD_SIZE) {
                    fprintf(stderr, "[FHOS-Kernel] Payload too large (%u bytes)\n", payload_len);
                    response_status = 0xE004;
                } else if (payload_len > 0) {
                    payload = malloc(payload_len + 1);
                    if (payload) {
                        if (recv_exact(client_fd, payload, payload_len) == (ssize_t)payload_len) {
                            payload[payload_len] = '\0';
                            printf("[FHOS-Kernel] Received payload: %s\n", payload);
                        } else {
                            response_status = 0xE001;
                        }
                    } else {
                        response_status = 0xE004;
                    }
                }

                fhos_ipc_header_t res_header;
                res_header.magic       = htonl(FHOS_IPC_MAGIC);
                res_header.version     = FHOS_IPC_VERSION;
                res_header.msg_type    = req_header.msg_type + 1;
                res_header.status_code = htons(response_status);
                res_header.payload_len = htonl(0);
                res_header.reserved    = htonl(0);

                send(client_fd, &res_header, sizeof(res_header), MSG_NOSIGNAL);

                if (payload) free(payload);
            }
        }
        close(client_fd);
    }
    close(listen_fd);
    unlink(IPC_SOCKET_PATH);
}

int main(void) {
    printf("=== Fusion Hero OS - IPC Bridge Server (MVP) ===\n");
    start_ipc_server();
    return 0;
}