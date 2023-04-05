## Objective
[trippa](https://github.com/Mautriz/trippa) is a python library for *resolving online features* easily in a type-safe and fine-grained way

More specifically, you define a feature as a simple python function, ask for it's dependencies in the function itself, 
trippa will handle the graph resolution, no feature will ever be computed twice and all features asked will be typed so that the code is 
less buggy and easier to maintain and expand upon

Other than that, **only the requested features and their dependencies will be computed**

It is **dependency-free** and REALLY small as it's just designed 
to do as little as possible and generalize in an easy to comprehend way 


## Installation
You can install trippa just like any other library using pip or whatever package manager you are using 
```bash
pip install trippa
```

## Basics

The first thing you want to do is define some features, we will just make a simple example

```python
from trippa import feature

@feature()
def fullname(info: Info) -> str:
    return "Mauro Insacco"
```

As we can see, it is a simple python function, taking in a context which is currently unused  

The function itself doesn't do much, it just returns a literal string, it would make sense to have some inputs or dependencies

```python
from trippa import input_feature

@input_feature()
def name() -> str:
    ...

@input_feature()
def surname() -> str:
    ...
```
**Everything** in trippa is a feature, even inputs, we define `name` and `surname` as input_features 
to make it clear that those must be provided by the client, let's now use them in the fullname resolver

```python
@feature()
async def fullname(info: Info) -> str:
    name_ = await info.resolve(name)
    surname_ = await info.resolve(surname)

    return f"{name_} {surname_}"
```
The feature became async, and requested the name and surname from the context, 
both results will be typed correctly as `str`'s, trippa will handle the resolution, just use them as you want 

Now to get the result
```python
from trippa import Trippa
from .features import name, surname, fullname

trippa = Trippa([name, surname, fullname])
res = trippa.start()

# inputs can be given both by string or feature reference
fullname_ = await res.input({name: "Mauro", "surname": "Insacco"}).resolve(fullname) 
assert fullname_ == "Mauro Insacco"
```

## Real World Example
The above example seems like an overkill for something so simple, let's emulate a real world use case  

- We have an `id`
- We want to retrieve some user information associated with that id 
- Then call some some external services that needs that user information to retrieve some more specific data 
about the person
- Extract some features from that raw data


```python
### context.py

# You can have custom context inside of your resolvers
class Context:
    user_api: UserApi
    vehicle_api: VehicleApi

    @classmethod
    def new(cls) -> Context:
        ...
```

```python
### features.py
@input_feature()
def id() -> str:
    ...

class UserInfo:
    name: str
    fiscal_code: str
    age: int

# No one stops you from using external calls or async code in general
# Everything can and should be a feature, it doesn't cost anything and simplifies reasoning
@feature()
async def user_info(info: Info[Context]) -> UserInfo:
    id_ = await info.resolve(id)
    return await info.ctx.user_api.get_user_info_by_id(id_)


class VehicleInfo:
    plate_number: str
    purchase_date: datetime
    value: float

# You can use the `meta` field to add metadata to feature definitions
# so that you can then use those to simplify your result post-processing
#
# Ex: wheter to export to DB or not some feature
# that might just be some raw data
@feature(meta={"export": False}) 
async def vehicles(info: Info[Context]) -> list[VehicleInfo]:
    user_info_ = await info.resolve(user_info)
    vehicles = await info.ctx.vehicle_api.get_person_vehicles(user_info_.fiscal_code)
    return vehicles if vehicles else []


# Features derived from the `raw` data from the external service.

# features are cheap, dont worry about being too granular, an unified definition 
# is always better than having to rewrite the same thing in multiple places in the future 
@feature()
async def number_of_vehicles(info: Info[Context]) -> int:
    vehicles_ = await info.resolve(vehicles)
    return len(vehicles_)


@feature()
async def max_vehicle_value(info: Info[Context]) -> float:
    vehicles_ = await info.resolve(vehicles)
    return max(veh.value for veh in vehicles_) if vehicles_ else 0


@feature(meta={"export": False})
async def family_members(info: Info[Context]) -> list[UserInfo]:
    user_info_ = await info.resolve(user_info)
    return await info.ctx.user_api.get_family_members(user_info_.fiscal_code)

@feature()
async def min_family_age(info: Info[Context]) -> int:
    user_info_ = await info.resolve(user_info)
    family_members_ = await info.resolve(family_members)
    return min(person.age for person in [user_info_, *family_members_])

@feature()
async def risk_factor(info: Info[Context]) -> float:
    min_family_age_ = await info.resolve(min_family_age)
    max_vehicle_value_ = await info.resolve(max_vehicle_value)
    
    # These could be features as well
    # It always depends on wheter the definition is reused
    # and what makes sense based on your business requirements
    # Features are cheap anyways
    age_risk = 100 - min_family_age_
    value_risk = max_vehicle_value_ / 100

    return age_risk * value_risk
```

```python
### main.py
from trippa import Trippa

import .features as features
from .context import Context
from .features import risk_factor, id, max_vehicle_value

# We can feed trippa the feature definitions by just giving the modules
trippa = Trippa.from_modules([features]).start(Context.new())

# Add inputs
trippa.input({id: "user_id"})

# Here we ask for the risk factor
risk_factor_ = await trippa.resolve(risk_factor)

# We can ask for anything we want, nothing will be recomputed.
max_vehicle_value_ = await trippa.resolve(max_vehicle_value)

```

## Contributing

### Installation
- Clone the [GitHub](https://github.com/Mautriz/trippa) repository!
- Have
    - python 3.10+
    - poetry
    - make
- Run: `make install`
- Develop
- Run: `make check`
- Profit
### Otherwise
If you dont want to install any of the above specifically, you can just use the `.devcontainer` configuration and 
run the repo from vscode `Dev Containers` extension or any service that provides development containers (`Github Codespaces`) 
