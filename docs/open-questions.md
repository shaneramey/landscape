### Open questions
- How can we generate a helm starter chart by prompting the user, such as:
```
Number of containers? [1] 3
  Container 1: number of volume mounts [0]
    Volume mount 1 name: ["volmount1"]
```

If this were possible, it might allow dynamically generated helm charts (just plug in your app)