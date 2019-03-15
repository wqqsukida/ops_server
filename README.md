# ops_server

##### down load ops_server
```bash
[root@localhost opt]# mkdir ops
[root@localhost opt]# ls
ops  rh
[root@localhost opt]# cd ops/
[root@localhost ops]# git clone https://github.com/wqqsukida/ops_server.git
```
##### install python3
```bash
[root@localhost pkg]# wget https://www.python.org/ftp/python/3.5.1/Python-3.5.1.tgz
[root@localhost pkg]# tar xvf Python-3.5.1.tgz 
[root@localhost pkg]# cd /opt/pkg/Python-3.5.1/
[root@localhost Python-3.5.1]# ./configure --prefix=/usr/local/src/python3
[root@localhost Python-3.5.1]# make && make install
[root@localhost Python-3.5.1]# ln -s /usr/local/src/python3/bin/python3 /usr/bin/python3
[root@localhost Python-3.5.1]# ln -s /usr/local/src/python3/bin/pip3 /usr/bin/pip3

```
##### get yum
```bash
wget -O /etc/yum.repos.d/epel.repo http://mirrors.aliyun.com/repo/epel-7.repo
wget -O /etc/yum.repos.d/CentOS-Base.repo http://mirrors.aliyun.com/repo/Centos-7.repo
```
##### install python pkg
```
pip3 install --upgrade pip
[root@localhost ops_server]# pip3 install -r requirements.txt 

[root@localhost ops_server]# ln -s /usr/local/src/python3/bin/gunicorn /usr/bin/gunicorn  
[root@localhost ops_server]# ln -s /usr/local/src/python3/bin/gunicorn_paster /usr/bin/gunicorn_paster
```
##### create database
```sql
MariaDB [(none)]> create database ops_server character set utf8;
Query OK, 1 row affected (0.00 sec)

MariaDB [(none)]> show databases;
+--------------------+
| Database           |
+--------------------+
| information_schema |
| mysql              |
| ops_server         |
| performance_schema |
| test               |
+--------------------+
5 rows in set (0.00 sec)

```
##### import database
```bash
[root@localhost ops_server]# python3 manage.py makemigrations
[root@localhost ops_server]# python3 manage.py migrate
```
##### start nginx
```bash
[root@localhost nginx]# mv nginx.conf nginx.conf.bak
[root@localhost nginx]# vim nginx.conf
```
```
# For more information on configuration, see:
#   * Official English Documentation: http://nginx.org/en/docs/
#   * Official Russian Documentation: http://nginx.org/ru/docs/

user root;
worker_processes auto;
error_log /var/log/nginx/error.log;
pid /run/nginx.pid;

# Load dynamic modules. See /usr/share/nginx/README.dynamic.
include /usr/share/nginx/modules/*.conf;

events {
    worker_connections 1024;
}

http {
    log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for"';

    access_log  /var/log/nginx/access.log  main;

    sendfile            on;
    tcp_nopush          on;
    tcp_nodelay         on;
    keepalive_timeout   65;
    types_hash_max_size 2048;

    include             /etc/nginx/mime.types;
    default_type        application/octet-stream;

    # Load modular configuration files from the /etc/nginx/conf.d directory.
    # See http://nginx.org/en/docs/ngx_core_module.html#include
    # for more information.
    include /etc/nginx/conf.d/*.conf;

    server {
        listen       80 ;
        server_name  www.deraops.com;
	server_name  0.0.0.0;
        # root         /usr/share/nginx/html;

        # Load configuration files for the default server block.
        include /etc/nginx/default.d/*.conf;

        location / {
	    proxy_pass http://127.0.0.1:8000;
	    proxy_set_header Host $host;
	    proxy_set_header X-Real-IP $remote_addr;
	    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
	    proxy_set_header X-Forwarded-Proto $scheme;
            client_max_body_size 200m;
	    proxy_connect_timeout 300s;
	    proxy_send_timeout 300s;
     	    proxy_read_timeout 300s;
	}
	
	location /static {
	    alias /$YOUR_PROJECT_PATH/ops_server/static;
        }

    }

# Settings for a TLS enabled server.
#
#    server {
#        listen       443 ssl http2 default_server;
#        listen       [::]:443 ssl http2 default_server;
#        server_name  _;
#        root         /usr/share/nginx/html;
#
#        ssl_certificate "/etc/pki/nginx/server.crt";
#        ssl_certificate_key "/etc/pki/nginx/private/server.key";
#        ssl_session_cache shared:SSL:1m;
#        ssl_session_timeout  10m;
#        ssl_ciphers HIGH:!aNULL:!MD5;
#        ssl_prefer_server_ciphers on;
#
#        # Load configuration files for the default server block.
#        include /etc/nginx/default.d/*.conf;
#
#        location / {
#        }
#
#        error_page 404 /404.html;
#            location = /40x.html {
#        }
#
#        error_page 500 502 503 504 /50x.html;
#            location = /50x.html {
#        }
#    }

}

```
```bash
[root@localhost nginx]# systemctl start nginx
[root@localhost nginx]# systemctl status nginx
```
##### settings
```python
DEBUG = True

ALLOWED_HOSTS = ["*"]

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
    'ENGINE': 'django.db.backends.mysql',
    'NAME':'ops_server',
    'USER': 'root',
    'PASSWORD': '',
    'HOST': 'localhost',
    'PORT': '3306',
    }
}

###############################其它设置##################################
SERVER_IP = 'YOURT SERVER_IP'
CODE_FONT_FILE = 'FONT FILE PATH'
##################### Nvme Settings ###################################

SMART_LOG_LIMIT_TIME = 0.1    #数据库保留smart_log天数
SSD_RECORD = 7  # SSD相关记录保存最大天数

##################### 分页器设置 ########################################

PER_PAGE = 20    #每页显示数据数
PAGER_PAGE_COUNT = 11    #页面上最多显示页码数

##################### session配置 ######################################
SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # 引擎（默认）
SESSION_COOKIE_NAME = "sessionid"  # Session的cookie保存在浏览器上时的key，即：sessionid=随机字符串（默认）
SESSION_COOKIE_PATH = "/"  # Session的cookie保存的路径（默认）
SESSION_COOKIE_DOMAIN = None  # Session的cookie保存的域名（默认）
SESSION_COOKIE_SECURE = False  # 是否Https传输cookie（默认）
SESSION_COOKIE_HTTPONLY = True  # 是否Session的cookie只支持http传输（默认）
# SESSION_COOKIE_AGE = 3600  # Session的cookie失效日期（1小时）（默认1209600 2周）
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # 是否关闭浏览器使得Session过期（默认False）
SESSION_SAVE_EVERY_REQUEST = True  # 是否每次请求都保存Session，默认修改之后才保存（默认False）

#################### django-crontab ####################################
CRONJOBS = [
    ('*/30 * * * *','cmdb.cron_task.refresh_server','>> /tmp/cmdb_refresh.log')
]
```
##### run server
```bash
[root@localhost ops_server]# python3 manage.py crontab add
[root@localhost ops_server]# gunicorn -w 6 -k gevent -b 0.0.0.0:8000 ops_server.wsgi:application
```

