#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import sys
import os
import json
import time
import requests
import getopt


def save_version(data, file):
    data['kubernetes'] = list(set(data.get("kubernetes")))
    data['etcd'] = list(set(data.get("etcd")))
    data['docker'] = list(set(data.get("docker")))
    data['cni'] = list(set(data.get("cni")))
    data['containerd'] = list(set(data.get("containerd")))
    data['crictl'] = list(set(data.get("crictl")))
    data['runc'] = list(set(data.get("runc")))
    with open(file, "w") as f:
        json.dump(data, f)


def timestamp_to_time(timestamp):
    time_local = time.localtime(int(timestamp))
    return time.strftime("%Y-%m-%d %H:%M:%S", time_local)


def download(url, path):
    print(url, path)
    start = time.time()
    size = 0
    chunk_size = 1024
    req = requests.get(url, stream=True)
    content_size = int(req.headers.get("content-length"))
    try:
        if req.status_code == 200:
            with open(path, 'wb') as file:
                # print("文件大小：%0.2f MB" % (content_size / chunk_size / 1024))
                for data in req.iter_content(chunk_size=chunk_size):
                    file.write(data)
                    size += len(data)
                    print("\r" + "[下载进度]: %s %.2f%%" % (
                        '>' * int(size * 50 / content_size), float(size / content_size * 100)))
        else:
            return False
        end = time.time()
        print("\n下载完成，用时：%.2f s" % (end - start))
        return True
    except Exception as e:
        print(e)
        return False


if __name__ == "__main__":
    if os.path.exists("version.json"):
        with open("version.json", 'r') as file:
            version_dict = json.load(file)
    else:
        version_dict = {
            "etcd": [],
            "docker": [],
            "kubernetes": [],
            "cni": [],
            "containerd": [],
            "crictl": [],
            "runc": []
        }

    kubernetes_list = [
        "kube-apiserver",
        "kube-controller-manager",
        "kube-scheduler",
        "kubectl",
        "kube-proxy",
        "kubelet"
    ]
    etcd_version = ""
    cni_version = ""
    kubernetes_version = ""
    docker_version = ""

    opts, args = getopt.getopt(sys.argv[1:], "he:c:k:d:", ["etcd=", "cni=", "kubernetes=", "docker="])
    for opt, arg in opts:
        if opt == '-h':
            print('main.py -e <etcd version> -c <cni version> -k <kubernetes version> -d <docker version>')
            sys.exit()
        elif opt in ("-e", "--etcd"):
            etcd_version = arg
        elif opt in ("-c", "--cni"):
            cni_version = arg
        elif opt in ("-k", "--kubernetes"):
            kubernetes_version = arg
        elif opt in ("-d", "--docker"):
            docker_version = arg

    if etcd_version != "" or cni_version != "" or kubernetes_version != "" or cni_version != "":
        for name in kubernetes_list:
            print("开始下载: %s" % (name))
            print("https://storage.googleapis.com/kubernetes-release/release/%s/bin/linux/amd64/%s" % (
                kubernetes_version, name))
            path = "package/kubernetes-release/release/%s/bin/linux/amd64" % (kubernetes_version)
            os.makedirs(path, exist_ok=True)
            r = download(
                url="https://storage.googleapis.com/kubernetes-release/release/%s/bin/linux/amd64/%s" % (
                    kubernetes_version, name),
                path=path + "/" + name
            )
            if r:
                version_dict.get("kubernetes").append(kubernetes_version)
            with open("version.json", "w") as f:
                json.dump(version_dict, f)
        sys.exit(0)

    # etcd
    req = requests.get("https://api.github.com/repos/coreos/etcd/releases")
    if req.status_code != 403:
        for release in json.loads(req.text):
            if release.get("tag_name").find("rc") == -1 and release.get("tag_name").find("beta") == -1 and release.get(
                    "tag_name").find("alpha") == -1:
                for assets in release.get("assets"):
                    if assets.get("name").find("linux-amd64") != -1 and assets.get("name").find("asc") == -1:
                        if release.get("tag_name") not in version_dict.get("etcd"):
                            path = "package/coreos/etcd/releases/download/%s" % release.get("tag_name")
                            os.makedirs(path, exist_ok=True)
                            print("开始下载: %s" % (assets.get("name")))
                            download(url=assets.get("browser_download_url"), path=path + "/" + assets.get("name"))
                            version_dict.get("etcd").append(release.get("tag_name"))
                            save_version(version_dict, "version.json")
                        else:
                            print("版本以同步(%s)，跳过..." % assets.get("name"))
    else:
        print("reset time: %s" % timestamp_to_time(req.headers.get("X-Ratelimit-Reset")))

    # docker
    req = requests.get("https://api.github.com/repos/moby/moby/releases")
    if req.status_code != 403:
        for release in json.loads(req.text):
            if release.get("tag_name").find("rc") == -1 and release.get("tag_name").find("beta") == -1 and release.get("tag_name").find("ce") == -1:
                if release.get("tag_name") not in version_dict.get("docker"):
                    path = "package/linux/static/stable/x86_64"
                    os.makedirs(path, exist_ok=True)
                    print("开始下载: %s" % (release.get("tag_name")))
                    r = download(
                        url="https://download.docker.com/linux/static/stable/x86_64/docker-%s.tgz" % release.get(
                            "tag_name").replace('v', ''),
                        path=path + "/docker-%s.tgz" % (release.get("tag_name").replace('v', ''))
                    )
                    if r:
                        version_dict.get("docker").append(release.get("tag_name"))
                    with open("version.json", "w") as f:
                        json.dump(version_dict, f)
                else:
                    print("版本以同步(%s)，跳过..." % release.get("tag_name"))
    else:
        print("reset time: %s" % timestamp_to_time(req.headers.get("X-Ratelimit-Reset")))

    # kubernetes
    req = requests.get("https://api.github.com/repos/kubernetes/kubernetes/releases")
    if req.status_code != 403:
        for release in json.loads(req.text):
            if release.get("tag_name").find("rc") == -1 and release.get("tag_name").find("beta") == -1 and release.get(
                    "tag_name").find("alpha") == -1:
                path = "package/kubernetes-release/release/%s/bin/linux/amd64" % (release.get("tag_name"))
                os.makedirs(path, exist_ok=True)
                if release.get("tag_name") not in version_dict.get("kubernetes"):
                    for name in kubernetes_list:
                        print("开始下载: %s, %s" % (release.get("tag_name"), name))
                        r = download(
                            url="https://storage.googleapis.com/kubernetes-release/release/%s/bin/linux/amd64/%s" % (
                                release.get("tag_name"), name),
                            path=path + "/" + name
                        )
                        if r:
                            version_dict.get("kubernetes").append(release.get("tag_name"))
                        with open("version.json", "w") as f:
                            json.dump(version_dict, f)
                else:
                    print("版本以同步(%s)，跳过..." % release.get("tag_name"))

    else:
        print("reset time: %s" % timestamp_to_time(req.headers.get("X-Ratelimit-Reset")))

    # CNI
    req = requests.get("https://api.github.com/repos/containernetworking/plugins/releases")
    if req.status_code != 403:
        for release in json.loads(req.text):
            if release.get("tag_name").find("rc") == -1 and release.get("tag_name").find("beta") == -1:
                for assets in release.get("assets"):
                    if assets.get("name").find("linux-amd64") != -1 and assets.get("name").find(
                            "asc") == -1 and assets.get("name").find("sha1") == -1:
                        if release.get("tag_name") not in version_dict.get("cni"):
                            path = "package/containernetworking/plugins/releases/download/%s" % release.get("tag_name")
                            os.makedirs(path, exist_ok=True)
                            print("开始下载: %s" % (assets.get("name")))
                            download(url=assets.get("browser_download_url"), path=path + "/" + assets.get("name"))
                            version_dict.get("cni").append(release.get("tag_name"))
                            save_version(version_dict, "version.json")
                        else:
                            print("版本以同步(%s)，跳过..." % assets.get("name"))
    else:
        print("reset time: %s" % timestamp_to_time(req.headers.get("X-Ratelimit-Reset")))

    # runc
    req = requests.get("https://api.github.com/repos/opencontainers/runc/releases")
    if req.status_code != 403:
        for release in json.loads(req.text):
            if release.get("tag_name").find("rc") == -1 and release.get("tag_name").find("beta") == -1:
                for assets in release.get("assets"):
                    if assets.get("name").find("asc") == -1 and assets.get("name").find("sha1") == -1 and assets.get(
                            "name").find("runc.amd64") != -1:
                        if release.get("tag_name") not in version_dict.get("runc"):
                            path = "package/opencontainers/runc/releases/download/%s" % release.get("tag_name")
                            os.makedirs(path, exist_ok=True)
                            print("开始下载: %s, 版本：%s" % (assets.get("name"), release.get("tag_name")))
                            download(url=assets.get("browser_download_url"), path=path + "/" + assets.get("name"))
                            version_dict.get("runc").append(release.get("tag_name"))
                            save_version(version_dict, "version.json")
                        else:
                            print("版本以同步(%s)，跳过..." % assets.get("name"))
    else:
        print("reset time: %s" % timestamp_to_time(req.headers.get("X-Ratelimit-Reset")))

    # containerd
    req = requests.get("https://api.github.com/repos/kubernetes-sigs/cri-tools/releases")
    if req.status_code != 403:
        for release in json.loads(req.text):
            if release.get("tag_name").find("rc") == -1 and release.get("tag_name").find("beta") == -1:
                for assets in release.get("assets"):
                    if assets.get("name").find("asc") == -1 and assets.get("name").find("sha") == -1 and assets.get(
                            "name").find("cri") == -1 and assets.get("name").find("linux-amd64") != -1:
                        if release.get("tag_name") not in version_dict.get("containerd"):
                            path = "package/kubernetes-sigs/cri-tools/releases/download/%s" % release.get("tag_name")
                            os.makedirs(path, exist_ok=True)
                            print("开始下载: %s, 版本：%s" % (assets.get("name"), release.get("tag_name")))
                            download(url=assets.get("browser_download_url"), path=path + "/" + assets.get("name"))
                            version_dict.get("containerd").append(release.get("tag_name"))
                            save_version(version_dict, "version.json")
                        else:
                            print("版本以同步(%s)，跳过..." % assets.get("name"))
    else:
        print("reset time: %s" % timestamp_to_time(req.headers.get("X-Ratelimit-Reset")))

    # crictl
    req = requests.get("https://api.github.com/repos/kubernetes-sigs/cri-tools/releases")
    if req.status_code != 403:
        for release in json.loads(req.text):
            if release.get("tag_name").find("rc") == -1 and release.get("tag_name").find("beta") == -1:
                for assets in release.get("assets"):
                    if assets.get("name").find("asc") == -1 and assets.get("name").find("sha") == -1 and assets.get(
                            "name").find("alpha") == -1 and assets.get("name").find("linux-amd64") != -1 and assets.get(
                        "name").find("critest") == -1:
                        if release.get("tag_name") not in version_dict.get("containerd"):
                            path = "package/kubernetes-sigs/cri-tools/releases/download/%s" % release.get("tag_name")
                            os.makedirs(path, exist_ok=True)
                            print("开始下载: %s, 版本：%s" % (assets.get("name"), release.get("tag_name")))
                            download(url=assets.get("browser_download_url"), path=path + "/" + assets.get("name"))
                            version_dict.get("crictl").append(release.get("tag_name"))
                            save_version(version_dict, "version.json")
                        else:
                            print("版本以同步(%s)，跳过..." % assets.get("name"))
    else:
        print("reset time: %s" % timestamp_to_time(req.headers.get("X-Ratelimit-Reset")))

    save_version(version_dict, "version.json")

