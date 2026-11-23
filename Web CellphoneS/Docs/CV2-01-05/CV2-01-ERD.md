# CV2-01 / CV2-04 – Sơ đồ ERD đề xuất

Sơ đồ được dựng từ các Link/Table trong source và ba Custom Field bổ sung. `CRM Lead`/`CRM Deal` vẫn cần đối chiếu metadata thực tế.

```mermaid
erDiagram
    C360_CUSTOMER ||--o{ CRM_LEAD : "custom_c360_customer"
    C360_CUSTOMER ||--o{ CRM_DEAL : "custom_c360_customer"
    CRM_LEAD ||--o{ CRM_DEAL : "lead"
    C360_CUSTOMER ||--o{ CUSTOMER_ORDER : "customer"
    CUSTOMER_ORDER ||--|{ CUSTOMER_ORDER_ITEM : "items / parent"
    C360_CUSTOMER ||--o{ CUSTOMER_SUPPORT_TICKET : "customer"
    CUSTOMER_ORDER o|--o{ CUSTOMER_SUPPORT_TICKET : "related_order (optional)"
    C360_CUSTOMER o|--o{ C360_CUSTOMER_INTAKE : "customer (confirmed)"
    C360_CUSTOMER o|--o{ C360_CUSTOMER_INTAKE : "candidate_customer (review)"
    CRM_LEAD o|--o| C360_CUSTOMER : "legacy crm_lead"

    C360_CUSTOMER {
        string name PK
        string customer_name
        string phone_number
        string email
        string crm_lead FK
    }
    CRM_LEAD {
        string name PK
        string custom_c360_customer FK
        string custom_consultation_notes
    }
    CRM_DEAL {
        string name PK
        string lead FK
        string custom_c360_customer FK
    }
    CUSTOMER_ORDER {
        string name PK
        string customer FK
        date order_date
    }
    CUSTOMER_ORDER_ITEM {
        string name PK
        string parent FK
        string parenttype
        string parentfield
    }
    CUSTOMER_SUPPORT_TICKET {
        string name PK
        string customer FK
        string related_order FK
    }
    C360_CUSTOMER_INTAKE {
        string name PK
        string source_key UK
        string source_channel
        string customer FK
        string candidate_customer FK
        string status
    }
```

**Quy tắc:** Một khách hàng có 0..n Lead, Deal, Order, Ticket và intake. Deal liên kết Customer trực tiếp hoặc qua Lead; khi có cả hai, Customer phải trùng. Ticket có `related_order` thì Order bắt buộc thuộc chính Customer đó. `crm_lead` được giữ để tương thích dữ liệu cũ, không phải nguồn duy nhất để tổng hợp.

**Ghi chú:** Mermaid thể hiện quan hệ logic, không phải toàn bộ khoá ngoại SQL vật lý; Frappe Link field không nhất thiết tạo ràng buộc FOREIGN KEY trong MariaDB. `Customer Order Item` thuộc Table của Order qua cột hệ thống `parent`.
