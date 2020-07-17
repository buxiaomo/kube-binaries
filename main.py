#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os
import json
import time
import requests


def save_version(data, file):
    data['kubernetes'] = list(set(data.get("kubernetes")))
    data['etcd'] = list(set(data.get("etcd")))
    data['docker'] = list(set(data.get("docker")))
    with open(file, "w") as f:
        json.dump(data, f)


def download(url, path):
    start = time.time()
    size = 0
    chunk_size = 1024
    req = requests.get(url, stream=True)
    content_size = int(req.headers.get("content-length"))
    if req.status_code == 200:
        with open(path, 'wb') as file:
            # print("文件大小：%0.2f MB" % (content_size / chunk_size / 1024))
            for data in req.iter_content(chunk_size=chunk_size):
                file.write(data)
                size += len(data)
                print("\r" + "[下载进度]: %s %.2f%%" % (
                    '>' * int(size * 50 / content_size), float(size / content_size * 100)), end='')
    else:
        return False
    end = time.time()
    print("\n下载完成，用时：%.2f s" % (end - start))
    return True


def timestamp_to_time(timestamp):
    time_local = time.localtime(int(timestamp))
    return time.strftime("%Y-%m-%d %H:%M:%S", time_local)


if __name__ == "__main__":
    if os.path.exists("version.json"):
        with open("version.json", 'r') as file:
            version_dict = json.load(file)
    else:
        version_dict = {
            "etcd": [],
            "docker": [],
            "kubernetes": [],
            "cni": []
        }

    # etcd
    req = requests.get("https://api.github.com/repos/coreos/etcd/releases")
    if req.status_code != 403:
        for release in json.loads(req.text):
            if release.get("tag_name").find("rc") == -1 and release.get("tag_name").find("beta") == -1:
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
    req = requests.get("https://api.github.com/repos/docker/docker-ce/releases")
    if req.status_code != 403:
        for release in json.loads(req.text):
            if release.get("tag_name").find("rc") == -1 and release.get("tag_name").find("beta") == -1:
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
    kubernetes_list = [
        "kube-apiserver",
        "kube-controller-manager",
        "kube-scheduler",
        "kubectl",
        "kube-proxy",
        "kubelet"
    ]
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
                    if assets.get("name").find("linux-amd64") != -1 and assets.get("name").find("asc") == -1 and assets.get("name").find("sha1") == -1:
                        if release.get("tag_name") not in version_dict.get("cni"):
                            path = "containernetworking/plugins/releases/download/%s" % release.get("tag_name")
                            os.makedirs(path, exist_ok=True)
                            print("开始下载: %s" % (assets.get("name")))
                            download(url=assets.get("browser_download_url"), path=path + "/" + assets.get("name"))
                            version_dict.get("cni").append(release.get("tag_name"))
                            save_version(version_dict, "version.json")
                        else:
                            print("版本以同步(%s)，跳过..." % assets.get("name"))
    else:
        print("reset time: %s" % timestamp_to_time(req.headers.get("X-Ratelimit-Reset")))


    save_version(version_dict, "version.json")