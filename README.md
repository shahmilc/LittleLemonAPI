# LittleLemonAPI
A backend REST API for restaurant order management applications, in this case, for a hypothetical restaurant 'Little Lemon'. The API allows for browsing of menu items and menu categories, addition of items to a cart, submission of the cart as an order, and management of the order through the assigning of delivery crews and status changes.

## Table of Contents

- [API Endpoints](#api-endpoints)
    - [User and Token Generation](#user-creation-and-token-generation-endpoints)
    - [Menu and Categories](#menu-and-category-endpoints)
    - [User Group Management](#user-group-management-endpoints)
    - [Cart and Orders](#cart-and-order-endpoints)
- [Authentication and Authorization layers](#authentication-and-authorization-layers)
- [Response format](#response-format)
- [Ordering and Search](#ordering-and-search)
- [Throttling](#throttling)
- [Pagination](#pagination)

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

## Authentication and Authorization layers

Users can register using the account registry endpoint, and use the registered username and password to retrieve an HTTP web token from the login endpoint. This token must be included as a Bearer token with the 'Token' prefix to make authenticated requests. This token does not expire.

The authorization layer uses Django roles to seperate user permissions. Admins are users created using Django's createsuperuser command. Managers are users with the 'Manager' role, Delivery crew are users with the 'Delivery crew' role, and Customers are authenticated users with no roles.

## Response format

Responses can be returned in JSON, XML, or TEXT/HTML (BrowsableAPIView) format. Use the `format` query string parameter to specify format, e.g. `/api/order?format=json`. Alternatively, specify the desired format in the `Accept` field of the request header.

## Ordering and Search

Ordering can be achieved on some endpoints using the BrowsableAPIView, or using the `ordering` query string parameter, e.g. `/api/orders?ordering=date` will sort orders by ascending date. To sort by descending date, use `-date`

Search can be achieved similarly, using the `search` query string parameter, e.g. `/api/menu-items?search=pasta`. The search query will run a case-insensitive 'contains' search across the search fields, which are prescribed for each endpoint below. 

The following endpoints have ordering and/or search functionality. The Ordering Options are the options you have to pass as the `ordering` query string parameter. The Search Fields are the fields across which a search query will look for the term:

| Endpoint | Ordering Options | Search Fields |
| --- | --- | --- |
| `/api/menu-items` | `price`, `-price`, `category`, `-category` | `title`, `category` |
| `/api/orders` | `user__username`, `-user__username`, `delivery_crew`, `-delivery_crew`, `status`, `-status`, `date`, `-date`, `total`, `-total` | `user__username`, `delivery_crew__username`, `orderitems` |

## Throttling

The default throttle rates are defined in settings.py under `REST_FRAMEWORK` as `DEFAULT_THROTTLE_RATES`. By default, all endpoints have the following throttle rates:

| User Permission | Throttle Rate |
| --- | --- |
| Anonymous | 50/hour |
| Authenticated | 30/minute |

## Pagination

All responses are paginated, with a default and max of 3 results per page. This max is defined in settings.py under `REST_FRAMEWORK` as `PAGE_SIZE`. Using the `page` query string parameter allows for the retrieval of a specific page, e.g. `/api/menu-items?page=2`. 

Using the `perpage` query string parameter allows to specify how many results per page (up to the max), e.g. `/api/menu-items?perpage=2&page=4`.
