# Providers
Providers are language-agnostic applications that provide fatstacks-compliant APIs so they can be used as backends for fatstacks. 

## Provider Structure
Providers should provide a RESTful JSON API that adheres to the fatstacks specifications. The key components of a provider include:
### / (root)
- **Method**: GET
- **Description**: Returns the application manifest (`App` schema) describing the application.

### /surfaces/<surface_id>
- **Method**: GET
- **Description**: Returns the surface manifest (`Surface` schema) for the specified surface ID.