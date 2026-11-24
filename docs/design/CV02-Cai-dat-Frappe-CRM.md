# 4.2. TRIỂN KHAI VÀ CÀI ĐẶT HỆ THỐNG FRAPPE CRM

## 4.2.1. Mục tiêu triển khai

Trong đồ án xây dựng hệ thống Customer 360 cho tình huống nghiên cứu CellphoneS, nhóm lựa chọn Frappe Framework kết hợp với Frappe CRM làm nền tảng phát triển và triển khai hệ thống.

Frappe Framework là nền tảng phát triển ứng dụng dựa trên Python, hỗ trợ quản lý cơ sở dữ liệu, người dùng, phân quyền và xây dựng các chức năng nghiệp vụ. Frappe CRM là ứng dụng được phát triển trên nền tảng Frappe, cung cấp các chức năng quản lý khách hàng tiềm năng (Lead), cơ hội bán hàng (Deal), thông tin liên hệ (Contact) và lịch sử tương tác với khách hàng.

Mục tiêu của công việc cài đặt gồm:

Thiết lập môi trường Frappe Framework và Frappe CRM hoạt động trên máy tính cá nhân.

Cấu hình các dịch vụ cần thiết để hệ thống có thể vận hành.

Khởi tạo cơ sở dữ liệu và site phục vụ đồ án.

Kiểm tra khả năng truy cập và đăng nhập hệ thống.

Chuẩn bị môi trường thống nhất để các thành viên tiếp tục cấu hình, phát triển và kiểm thử các chức năng Customer 360.

Nhóm lựa chọn phương pháp triển khai bằng Docker nhằm hạn chế sự khác biệt về môi trường giữa các máy tính, đồng thời thuận tiện trong việc quản lý và khởi động các dịch vụ.

Phạm vi triển khai là môi trường phát triển và trình diễn trên máy cục bộ (local development/demo), chưa phải môi trường vận hành chính thức.

## 4.2.2. Chuẩn bị môi trường cài đặt

### a. Công nghệ sử dụng

Các công nghệ và công cụ được sử dụng trong quá trình triển khai được trình bày trong Bảng 4.1.

Bảng 4.1. Công nghệ và công cụ triển khai

| Thành phần | Công nghệ | Vai trò |
| --- | --- | --- |
| Hệ điều hành | Windows 11 | Môi trường triển khai cục bộ |
| Nền tảng container | Docker Desktop | Chạy và quản lý các container |
| Công cụ điều phối | Docker Compose | Khởi tạo và điều phối các dịch vụ |
| Framework | Frappe Framework v15 | Nền tảng phát triển ứng dụng |
| Ứng dụng CRM | Frappe CRM – nhánh main | Quản lý nghiệp vụ CRM |
| Cơ sở dữ liệu | MariaDB | Lưu trữ dữ liệu |
| Dịch vụ hỗ trợ | Redis | Hỗ trợ cache và các tác vụ nội bộ |
| Python | 3.12.15 | Môi trường thực thi Frappe |
| Công cụ quản lý mã nguồn | Git | Quản lý và tải mã nguồn |
| Công cụ dòng lệnh | Windows PowerShell | Thực thi các lệnh cài đặt |

### b. Kiểm tra các công cụ cần thiết

Trước khi triển khai, nhóm cài đặt Docker Desktop và Git. Sau đó, mở Windows PowerShell để kiểm tra môi trường.

Các câu lệnh kiểm tra:

docker --version

docker compose version

git --version

docker version

Ý nghĩa của các câu lệnh:

docker --version: Kiểm tra Docker CLI đã được cài đặt.

docker compose version: Kiểm tra Docker Compose.

git --version: Kiểm tra Git.

docker version: Kiểm tra thông tin Docker Client và Docker Server.

Đặc biệt, kết quả của docker version cần hiển thị cả Client và Server, cho thấy Docker Engine đang hoạt động và sẵn sàng khởi tạo container.

Nếu Docker Server không phản hồi, cần mở Docker Desktop và chờ Docker Engine chuyển sang trạng thái Running.

Kết quả: Các công cụ được cài đặt và Docker Engine có thể sử dụng để triển khai hệ thống.

![Hình minh chứng 1](CV02-images/hinh-001.png)

## 4.2.3. Chuẩn bị thư mục dự án và file cấu hình

### a. Tạo thư mục triển khai

Nhóm tạo thư mục frappe-crm để lưu trữ các file cấu hình và script phục vụ quá trình triển khai.

Câu lệnh thực hiện:

cd $HOME

New-Item -ItemType Directory -Force frappe-crm

cd frappe-crm

Trong đó:

cd $HOME: Di chuyển đến thư mục người dùng trên Windows.

New-Item: Tạo thư mục dự án.

cd frappe-crm: Di chuyển vào thư mục vừa tạo.

Sau khi thực hiện, các file cấu hình của hệ thống được quản lý tập trung trong thư mục frappe-crm.

![Hình minh chứng 2](CV02-images/hinh-002.png)

### b. Chuẩn bị file docker-compose.yml

Docker Compose được sử dụng để khai báo và quản lý các dịch vụ của hệ thống.

Nhóm tải file cấu hình Docker Compose từ repository Frappe CRM bằng câu lệnh:

curl.exe -L https://raw.githubusercontent.com/frappe/crm/develop/docker/docker-compose.yml -o docker-compose.yml

Kiểm tra file sau khi tải:

Get-Item .\docker-compose.yml

File docker-compose.yml có nhiệm vụ định nghĩa các dịch vụ cần thiết, cấu hình kết nối giữa các container, cổng truy cập và các tài nguyên phục vụ hệ thống.

Trong môi trường triển khai của nhóm, các dịch vụ chính bao gồm:

frappe: Chạy Frappe Framework và Frappe CRM.

mariadb: Quản lý cơ sở dữ liệu.

redis: Hỗ trợ các dịch vụ nội bộ.

Kết quả: File docker-compose.yml được chuẩn bị trong thư mục dự án, làm cơ sở để Docker Compose khởi tạo hệ thống.

![Hình minh chứng 3](CV02-images/hinh-003.png)

![Hình minh chứng 4](CV02-images/hinh-004.png)

## 4.2.4. Xây dựng script khởi tạo Frappe CRM

### a. Mục đích sử dụng init.sh

Để tự động hóa quá trình cài đặt, nhóm sử dụng file init.sh.

Script này thực hiện các nhiệm vụ:

Thiết lập môi trường Python.

Khởi tạo Frappe Bench.

Cấu hình kết nối MariaDB và Redis.

Tải và cài đặt ứng dụng Frappe CRM.

Khởi tạo site crm.localhost.

Thiết lập các cấu hình cần thiết.

Khởi động hệ thống.

Việc sử dụng script giúp giảm thao tác thủ công và bảo đảm quá trình cài đặt có thể được thực hiện theo cùng một quy trình trên các máy tính.

![Hình minh chứng 5](CV02-images/hinh-005.png)

### b. Thiết lập môi trường Python

Trong file init.sh, nhóm sử dụng các câu lệnh:

#!/bin/bash

set -e

export PYENV_VERSION=3.12.15

Giải thích:

#!/bin/bash: Chỉ định Bash là môi trường thực thi script.

set -e: Dừng script nếu một câu lệnh quan trọng thực thi thất bại.

PYENV_VERSION=3.12.15: Sử dụng phiên bản Python đã được nhóm kiểm thử tương thích với môi trường Frappe v15.

Trong quá trình triển khai, nhóm đã gặp vấn đề liên quan đến phụ thuộc phiên bản Python và ứng dụng bổ sung. Vì vậy, việc xác định phiên bản Python phù hợp là cần thiết để bảo đảm quá trình cài đặt ổn định.

![Hình minh chứng 6](CV02-images/hinh-006.png)

### c. Cấu hình MariaDB client

Nhóm bổ sung cấu hình MariaDB client để xử lý vấn đề kết nối SSL trong môi trường local.

Đoạn cấu hình quan trọng:

cat > /home/frappe/.my.cnf <<'EOF'

[client]

skip-ssl

EOF

chmod 600 /home/frappe/.my.cnf

Trong đó:

.my.cnf: File cấu hình MariaDB client.

skip-ssl: Không yêu cầu SSL đối với kết nối MariaDB trong môi trường local của nhóm.

chmod 600: Giới hạn quyền truy cập file cấu hình.

Cấu hình này được sử dụng để khắc phục lỗi kết nối giữa Frappe và MariaDB khi phía client yêu cầu SSL nhưng dịch vụ cơ sở dữ liệu local chưa được cấu hình TLS.

![Hình minh chứng 7](CV02-images/hinh-007.png)

### d. Kiểm tra Frappe Bench đã tồn tại

Script bổ sung cơ chế kiểm tra nhằm tránh khởi tạo lại Frappe Bench mỗi khi container được khởi động.

if [ -d "/home/frappe/frappe-bench/apps/frappe" ]; then

echo "Bench already exists, skipping init"

cd /home/frappe/frappe-bench

bench start

exit 0

fi

Đoạn lệnh kiểm tra sự tồn tại của thư mục ứng dụng Frappe.

Nếu Bench đã được tạo, script bỏ qua các bước cài đặt ban đầu và trực tiếp khởi động hệ thống bằng bench start.

Cơ chế này giúp tiết kiệm thời gian khi sử dụng lại môi trường và hạn chế việc khởi tạo trùng lặp.

![Hình minh chứng 8](CV02-images/hinh-008.png)

### e. Khởi tạo Frappe Bench

Câu lệnh thực hiện:

bench init --skip-redis-config-generation frappe-bench --version version-15

Lệnh bench init tạo môi trường Frappe Bench mới với tên frappe-bench.

Các tham số:

--version version-15: Sử dụng Frappe Framework phiên bản 15.

--skip-redis-config-generation: Bỏ qua việc tự tạo cấu hình Redis mặc định để sử dụng Redis được triển khai bằng Docker.

Sau khi khởi tạo, nhóm di chuyển vào thư mục Bench:

cd frappe-bench

Frappe Bench là môi trường quản lý ứng dụng, site và các dịch vụ cần thiết của Frappe Framework.

![Hình minh chứng 9](CV02-images/hinh-009.png)

### f. Cấu hình kết nối MariaDB và Redis

Sau khi tạo Bench, nhóm thiết lập các địa chỉ dịch vụ:

bench set-mariadb-host mariadb

bench set-redis-cache-host redis://redis:6379

bench set-redis-queue-host redis://redis:6379

bench set-redis-socketio-host redis://redis:6379

Các lệnh trên có nhiệm vụ:

set-mariadb-host: Xác định dịch vụ cơ sở dữ liệu MariaDB.

set-redis-cache-host: Cấu hình Redis cho bộ nhớ đệm.

set-redis-queue-host: Cấu hình Redis phục vụ hàng đợi tác vụ.

set-redis-socketio-host: Cấu hình Redis phục vụ các chức năng liên quan đến giao tiếp thời gian thực.

Trong Docker Compose, các container có thể kết nối với nhau thông qua tên dịch vụ như mariadb và redis.

Nhóm tiếp tục điều chỉnh file Procfile:

sed -i '/redis/d' ./Procfile

sed -i '/watch/d' ./Procfile

Việc điều chỉnh nhằm loại bỏ các tiến trình Redis và watch mặc định không cần thiết trong cấu hình chạy của nhóm.

![Hình minh chứng 10](CV02-images/hinh-010.png)

### g. Tải ứng dụng Frappe CRM

bench get-app crm --branch main

Sau khi chuẩn bị môi trường Framework, nhóm tiến hành tải ứng dụng CRM.

Câu lệnh:

Lệnh này tải mã nguồn Frappe CRM từ nhánh main vào môi trường Bench.

Đây là bước bổ sung ứng dụng CRM vào nền tảng Frappe Framework, tạo điều kiện triển khai các chức năng quản lý khách hàng.

### h. Khởi tạo site

Nhóm tạo site với tên crm.localhost.

Câu lệnh chính:

bench new-site crm.localhost \

--force \

--mariadb-root-password <DB_ROOT_PASSWORD> \

--admin-password <ADMIN_PASSWORD> \

--no-mariadb-socket

Trong đó:

crm.localhost: Tên site sử dụng trong môi trường local.

--mariadb-root-password: Mật khẩu quản trị cơ sở dữ liệu.

--admin-password: Mật khẩu quản trị Frappe.

--no-mariadb-socket: Sử dụng kết nối cơ sở dữ liệu qua mạng thay vì Unix socket.

Hai giá trị mật khẩu trong đoạn lệnh được thay bằng thông tin cấu hình của môi trường triển khai.

Sau khi tạo site, nhóm tiến hành cài đặt ứng dụng CRM:

bench --site crm.localhost install-app crm

Đây là câu lệnh quan trọng, thực hiện việc cài đặt ứng dụng Frappe CRM vào site đã khởi tạo.

### i. Thiết lập cấu hình hệ thống

Nhóm sử dụng các câu lệnh:

bench --site crm.localhost set-config developer_mode 1

bench --site crm.localhost set-config mute_emails 1

bench --site crm.localhost set-config server_script_enabled 1

bench --site crm.localhost clear-cache

bench use crm.localhost

Ý nghĩa:

developer_mode 1: Bật chế độ phát triển để hỗ trợ tùy chỉnh hệ thống.

mute_emails 1: Tạm thời tắt gửi email trong giai đoạn cài đặt ban đầu.

server_script_enabled 1: Cho phép sử dụng Server Script.

clear-cache: Làm mới bộ nhớ đệm của site.

bench use crm.localhost: Chọn site mặc định cho Bench.

Các cấu hình trên phục vụ giai đoạn phát triển và kiểm thử. Chức năng email có thể được bật lại trong công việc cấu hình hệ thống tiếp theo.

Cuối cùng, nhóm sử dụng:

bench start

Lệnh này khởi động các tiến trình cần thiết để hệ thống Frappe hoạt động.

![Hình minh chứng 11](CV02-images/hinh-011.png)

![Hình minh chứng 12](CV02-images/hinh-012.png)

## 4.2.5. Kiểm tra định dạng và tính hợp lệ của script

Do môi trường soạn thảo là Windows nhưng script được thực thi trong Linux container, nhóm cần bảo đảm file init.sh sử dụng định dạng xuống dòng LF thay vì CRLF.

Để kiểm tra, nhóm sử dụng PowerShell:

Get-Item .\init.sh

Select-String -Path .\init.sh -Pattern "PYENV_VERSION"

Select-String -Path .\init.sh -Pattern "whatsapp"

Các câu lệnh được sử dụng để kiểm tra file tồn tại, xác nhận cấu hình Python và bảo đảm script không chứa lệnh cài ứng dụng WhatsApp không cần thiết.

Kiểm tra định dạng xuống dòng:

$content = [System.IO.File]::ReadAllText(

(Resolve-Path .\init.sh)

)

if ($content.Contains("`r")) {

"LOI: file con ky tu CR"

} else {

"OK: LF only"

}

Kết quả mong đợi là OK: LF only.

Việc kiểm tra định dạng file giúp tránh lỗi thực thi script như No such command 'start\r'.

![Hình minh chứng 13](CV02-images/hinh-013.png)

## 4.2.6. Khởi động hệ thống bằng Docker Compose

Sau khi chuẩn bị đầy đủ các file cấu hình, nhóm tiến hành khởi động hệ thống.

### a. Khởi động container

Câu lệnh:

docker compose up -d

Lệnh này yêu cầu Docker Compose tạo và khởi động các dịch vụ đã được khai báo trong file docker-compose.yml.

Tham số -d cho phép các container chạy ở chế độ nền.

### b. Kiểm tra trạng thái container

Câu lệnh:

docker compose ps

Hệ thống của nhóm gồm ba container chính:

| Container | Dịch vụ | Trạng thái mong đợi |
| --- | --- | --- |
| crm-frappe-1 | Frappe CRM | Up |
| crm-mariadb-1 | MariaDB | Up |
| crm-redis-1 | Redis | Up |

Trạng thái Up cho thấy container đang hoạt động. Tuy nhiên, để xác nhận ứng dụng được cài đặt hoàn chỉnh, nhóm tiếp tục kiểm tra log và danh sách ứng dụng.

![Hình minh chứng 14](CV02-images/hinh-014.png)

![Hình minh chứng 15](CV02-images/hinh-015.png)

### c. Theo dõi quá trình cài đặt

Nhóm sử dụng câu lệnh:

docker compose logs -f frappe

Lệnh này hiển thị log của dịch vụ Frappe theo thời gian thực.

Một số thông báo quan trọng được sử dụng để xác định tiến độ cài đặt:

Creating new bench...

Getting frappe

Installing frappe

SUCCESS: Bench frappe-bench initialized

Getting crm

Installing crm

Updating DocTypes for crm: 100%

Current Site set to crm.localhost

Các thông báo trên lần lượt phản ánh quá trình khởi tạo Framework, tải ứng dụng CRM, cập nhật cấu trúc dữ liệu và lựa chọn site.

Trong giai đoạn cài đặt ban đầu, một số bước tải thư viện có thể mất thời gian nhưng không liên tục xuất hiện log. Vì vậy, nhóm theo dõi tiến trình thay vì khởi động lại ngay khi chưa thấy thông báo mới.

Hình 4.4. Log cài đặt Frappe Framework và Frappe CRM

![Hình minh chứng 16](CV02-images/hinh-016.png)

## 4.2.7. Xác minh kết quả cài đặt

Sau khi hoàn tất quá trình cài đặt, nhóm thực hiện các bước kiểm tra nhằm xác nhận hệ thống hoạt động đúng.

### a. Kiểm tra các tiến trình

Trong log của dịch vụ Frappe, các tiến trình quan trọng cần được khởi động bao gồm:

web.1 started

socketio.1 started

schedule.1 started

worker.1 started

Trong đó:

web: Phục vụ các yêu cầu truy cập ứng dụng.

socketio: Hỗ trợ giao tiếp thời gian thực.

schedule: Quản lý các tác vụ theo lịch.

worker: Xử lý các tác vụ nền.

### b. Kiểm tra ứng dụng đã cài đặt

Nhóm sử dụng câu lệnh:

docker compose exec frappe bash -lc "cd /home/frappe/frappe-bench && bench --site crm.localhost list-apps"

Lệnh này truy cập container Frappe và liệt kê các ứng dụng đã được cài đặt trên site crm.localhost.

Kết quả cần có hai ứng dụng:

frappe

crm

Điều này xác nhận Frappe Framework và Frappe CRM đã được cài đặt vào site.

Hình 4.5. Kết quả kiểm tra danh sách ứng dụng đã cài đặt

![Hình minh chứng 17](CV02-images/hinh-017.png)

### c. Truy cập giao diện CRM

Sau khi xác nhận các dịch vụ hoạt động, nhóm mở trình duyệt và truy cập:

http://crm.localhost:8000/crm

Nhóm đăng nhập bằng tài khoản quản trị đã được thiết lập khi khởi tạo site.

Kết quả cho thấy hệ thống hiển thị giao diện Frappe CRM và cho phép truy cập các chức năng chính như:

Leads

Deals

Contacts

Organizations

Tasks

Notes

Call Logs

Việc truy cập và sử dụng được giao diện CRM xác nhận môi trường triển khai đã sẵn sàng cho các công việc cấu hình và phát triển tiếp theo.

Hình 4.6. Giao diện Frappe CRM sau khi cài đặt thành công

![Hình minh chứng 18](CV02-images/hinh-018.png)

## 4.2.8. Các lỗi phát sinh và phương án khắc phục

Trong quá trình triển khai, nhóm gặp một số vấn đề kỹ thuật liên quan đến phiên bản phần mềm, kết nối cơ sở dữ liệu và môi trường thực thi.

Bảng 4.2. Tổng hợp các vấn đề và phương án xử lý

| Vấn đề | Nguyên nhân | Phương án xử lý |
| --- | --- | --- |
| Xung đột phụ thuộc ứng dụng WhatsApp | Ứng dụng yêu cầu phiên bản Frappe/Python khác với môi trường đang sử dụng | Loại bỏ bước cài WhatsApp và sử dụng Python 3.12.15 |
| Lỗi SSL khi kết nối MariaDB | MariaDB client yêu cầu SSL nhưng dịch vụ local không hỗ trợ TLS tương ứng | Bổ sung cấu hình skip-ssl |
| Thiếu bảng dữ liệu hệ thống | Quá trình tạo site bị gián đoạn | Khắc phục nguyên nhân gốc và khởi tạo lại môi trường cài mới khi chưa có dữ liệu cần giữ |
| Lỗi start\r | File shell script sử dụng CRLF | Chuyển file init.sh sang LF |
| Gián đoạn tải thư viện | Kết nối mạng không ổn định | Kiểm tra kết nối và theo dõi tiến trình cài đặt |

### a. Lỗi tương thích phiên bản

Trong quá trình cài đặt, nhóm gặp lỗi phụ thuộc khi sử dụng ứng dụng WhatsApp không tương thích với phiên bản Frappe/Python đã chọn.

Nhóm khắc phục bằng cách sử dụng Python 3.12.15 và loại bỏ lệnh tải ứng dụng WhatsApp khỏi script khởi tạo, do đây không phải thành phần bắt buộc của môi trường CRM hiện tại.

### b. Lỗi kết nối MariaDB

Thông báo lỗi:

SSL is required, but the server does not support it

Nhóm kiểm tra cấu hình MariaDB client và bổ sung tùy chọn skip-ssl trong môi trường local.

Sau khi điều chỉnh, quá trình tạo site có thể tiếp tục thực hiện.

### c. Lỗi định dạng script

Thông báo lỗi:

Table '...tabDefaultValue' doesn't exist

Table '...tabSingles' doesn't exist

Nguyên nhân là file init.sh chứa ký tự xuống dòng CRLF.

Nhóm chuyển định dạng file sang LF để phù hợp với môi trường Linux, sau đó khởi động lại dịch vụ Frappe.

### d. Lỗi cơ sở dữ liệu được tạo chưa hoàn chỉnh

Một số lỗi như:

Table '...tabDefaultValue' doesn't exist

Table '...tabSingles' doesn't exist

xuất hiện khi quá trình khởi tạo site hoặc cơ sở dữ liệu bị gián đoạn.

Đối với môi trường cài đặt mới chưa có dữ liệu cần giữ, nhóm có thể khắc phục nguyên nhân gốc và thực hiện khởi tạo lại.

Lưu ý: Lệnh docker compose down -v chỉ được sử dụng khi chủ động xóa dữ liệu để cài đặt lại từ đầu. Không sử dụng lệnh này đối với hệ thống đã lưu dữ liệu đồ án.

## 4.2.9. Quản lý và vận hành hệ thống sau cài đặt

Sau khi hệ thống được triển khai thành công, nhóm sử dụng Docker Compose để quản lý việc khởi động và dừng các dịch vụ.

### a. Dừng hệ thống

Khi kết thúc phiên làm việc, nhóm sử dụng:

docker compose stop

Lệnh này dừng các container mà không chủ động xóa volume dữ liệu.

### b. Khởi động lại hệ thống

Ở những lần sử dụng tiếp theo, nhóm mở Docker Desktop và thực hiện:

cd "$HOME\frappe-crm"

docker compose up -d

docker compose ps

Do môi trường Bench đã được tạo trước đó, script kiểm tra sự tồn tại của Frappe Bench và bỏ qua bước cài đặt ban đầu.

Thông báo mong đợi:

Bench already exists, skipping init

Sau đó, hệ thống tiếp tục khởi động các tiến trình web, socketio, schedule và worker.

Cơ chế này cho phép nhóm sử dụng lại môi trường CRM mà không cần cài đặt lại từ đầu.

## 4.2.10. Kết quả thực hiện

Sau quá trình triển khai, nhóm đã hoàn thành việc thiết lập môi trường Frappe CRM phục vụ đồ án Customer 360 cho CellphoneS.

Bảng 4.3. Tổng hợp kết quả triển khai

| STT | Nội dung | Kết quả |
| --- | --- | --- |
| 1 | Chuẩn bị môi trường Docker và Git | Hoàn thành |
| 2 | Chuẩn bị file Docker Compose | Hoàn thành |
| 3 | Xây dựng script khởi tạo | Hoàn thành |
| 4 | Khởi tạo Frappe Framework v15 | Hoàn thành |
| 5 | Cài đặt ứng dụng Frappe CRM | Hoàn thành |
| 6 | Khởi tạo site crm.localhost | Hoàn thành |
| 7 | Kết nối MariaDB và Redis | Hoàn thành |
| 8 | Khởi động các dịch vụ | Hoàn thành |
| 9 | Truy cập giao diện Frappe CRM | Thành công |
| 10 | Xây dựng hướng dẫn cài đặt cho nhóm | Hoàn thành |

Kết quả đạt được cho thấy hệ thống Frappe CRM đã được cài đặt và có thể vận hành trong môi trường local. Các dịch vụ cần thiết đã được cấu hình để hỗ trợ hoạt động của Framework và ứng dụng CRM.

Bên cạnh đó, nhóm đã xây dựng được quy trình triển khai có thể tái sử dụng, bao gồm các file cấu hình, script khởi tạo, câu lệnh vận hành và phương án xử lý những lỗi kỹ thuật thường gặp.

Kết luận: Công việc cài đặt đã hoàn thành mục tiêu xây dựng môi trường nền tảng cho đồ án. Hệ thống sẵn sàng phục vụ các công việc tiếp theo như cấu hình người dùng và phân quyền, thiết lập quy trình bán hàng, quản lý dữ liệu khách hàng và phát triển chức năng Customer 360.
