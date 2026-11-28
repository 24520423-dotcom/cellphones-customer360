# ERD Customer 360

```mermaid
erDiagram
    C360_CUSTOMER o|--o{ C360_SOURCE_RECORD : "nhận diện từ"
    C360_CUSTOMER ||--o{ CUSTOMER_ORDER : "mua"
    CUSTOMER_ORDER ||--|{ CUSTOMER_ORDER_ITEM : "gồm"
    C360_CUSTOMER ||--o{ CUSTOMER_SUPPORT_TICKET : "yêu cầu"
    CUSTOMER_ORDER o|--o{ CUSTOMER_SUPPORT_TICKET : "đơn liên quan"
    C360_CUSTOMER o|--o{ C360_CUSTOMER : "Golden Record"
    C360_CUSTOMER ||--o{ DYNAMIC_LINK : "bổ sung liên kết CRM"
    CONTACT o|--o{ C360_CUSTOMER : "Contact chính"
    CRM_LEAD o|--o{ C360_CUSTOMER : "Lead chính"
    CRM_LEAD o|--o{ CRM_DEAL : "chuyển thành"
    CRM_DEAL ||--o{ CRM_CONTACTS : "danh sách Contact"
    CONTACT ||--o{ CRM_CONTACTS : "được tham chiếu"
    CRM_DEAL o|--o{ CUSTOMER_ORDER : "liên kết khi đặt hàng"
    CUSTOMER_ORDER ||--o| CRM_TASK : "lịch chăm sóc"
    USER o|--o{ CUSTOMER_SUPPORT_TICKET : "được giao xử lý"
    USER o|--o{ CUSTOMER_ORDER : "phụ trách giao nhận"
```

`Dynamic Link` chỉ nhận Contact, CRM Lead và CRM Deal. Bản ghi nguồn có thể chưa gắn Customer trong khi chờ xác minh. Version và các sự kiện giữ tham chiếu tới tài liệu gốc và được lọc theo quyền trên Timeline.
