# LittleLemonAPI
Backend API for restaurant order management

## API Endpoints

### User creation and token generation endpoints

| Endpoint | Role | Method | Payload | Result |
| --- | --- | --- | --- | --- |
| `/token/login` | Any | `POST` | `username` and `password` | Returns an Auth Token if credentials valid |
| `/api/users` | Any | `POST` | `username`, `password`, optional `email` | Creates a new user with supplied credentials |
| `/api/users/me` | Any | `GET` | - | Returns information of current user |

### Menu and Category endpoints

| Endpoint | Role | Method | Payload | Result |
| --- | --- | --- | --- | --- |
| `/api/menu-items` | Any | `GET` | - | Returns all menu itmes |
| `/api/menu-items` | Manager | `POST` | `title`, `price`, `featured`, `category` | Adds a new menu item to the menu |
| `/api/menu-items/{menuItemId}` | Any | `GET` | - | Returns single menu item |
| `/api/menu-items/{menuItemId}` | Manager | `PUT` | `title`, `price`, `featured`, `category` | Replaces menu item |
| `/api/menu-items/{menuItemId}` | Manager | `PATCH` | Fields to be updated | Updates menu item by provided fields |
| `/api/menu-items/{menuItemId}` | Manager | `DELETE` | - | Deletes menu item |
| `/api/categories` | Manager | `GET` | - | Returns all menu categories |
| `/api/categories` | Manager | `POST` | `title` | Adds new category |
| `/api/categories/{categoryId}` | Manager | `PUT`, `PATCH` | `title` | Updates category |
| `/api/categories/{categoryId}` | Manager | `DELETE` | - | Deletes category (CASCADE deletes all related menu items) |

### User group management endpoints

| Endpoint | Role | Method | Payload | Result |
| --- | --- | --- | --- | --- |
| `/api/groups/manager/users` | Admin | `GET` | - | Returns list of Manager users |
| `/api/groups/manager/users` | Admin | `POST` | `username` | Gives the Manager role to the user with the supplied username |
| `/api/groups/manager/users/{userId}` | Admin | `DELETE` | - | Removes the Manager role from the user with userId |
| `/api/groups/delivery-crew/users` | Manager | `GET` | - | Returns list of all Delivery crew users |
| `/api/groups/delivery-crew/users` | Manager | `POST` | `username` | Gives the Delivery crew role to the user with the supplied username |
| `/api/groups/delivery-crew/users/{userId}` | Manager | `DELETE` | - | Removes the Delivery crew role from the user with userId |

### Cart and Order endpoints

| Endpoint | Role | Method | Payload | Result |
| --- | --- | --- | --- | --- |
| `/api/cart/menu-items` | Customer | `GET` | - | Returns current items in the cart for the current user token |
| `/api/cart/menu-items` | Customer | `POST` | `menuitemId` and `quantity` | Adds quantity of menuitem to user cart |
| `/api/cart/menu-items` | Customer | `DELETE` | - | Deletes cart |
| `/api/orders` | Customer | `GET` | - | Returns list of all Orders created by Customer |
| `/api/orders` | Manager | `GET` | - | Returns list of all Orders |
| `/api/orders` | Delivery crew | `GET` | - | Returns list of all Orders assigned to the Delivery crew |
| `/api/orders/{orderId}` | Customer, Manager, Delivery crew | `GET` | - | Returns single Order if user created order, is a Manager, or is a Delivery crew assigned to the Order |
| `/api/orders/{orderId}` | Manager | `PATCH` | `status` and/or `delivery_crew` | Updates Order status to 1 or 0, and/or updates assigned Delivery crew |
| `/api/orders/{orderId}` | Delivery crew | `PATCH` | `status` | Updates only Order status to 1 or 0 |
| `/api/orders/{orderId}` | Manager | `DELETE` | - | Deletes Order |