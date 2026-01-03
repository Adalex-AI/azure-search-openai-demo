# Additional documentation

Consult the main [README](../README.md) for general information about the project.
These are advanced topics that are not necessary for a basic deployment.

## Custom Features (This Fork)

See [CUSTOMIZATIONS_README.md](customizations/README.md) for documentation on:
- Citation sanitization for legal documents
- Dynamic category filtering
- Legal domain prompts
- Merge-safe architecture

### Legal Domain Evaluation

See [Legal Domain Evaluation](legal_evaluation.md) for comprehensive documentation on:
- Legal-specific evaluation metrics (statute citations, case law, terminology)
- Ground truth creation for UK CPR questions
- Azure Search index testing tools
- Running and interpreting legal evaluations

Historical development notes are archived in [docs/archive/development-history/](archive/development-history/README.md).

## Upstream Documentation

- Deploying:
  - [Troubleshooting deployment](docs/deploy_troubleshooting.md)
    - [Debugging the app on App Service](appservice.md)
  - [Deploying with azd: deep dive and CI/CD](azd.md)
  - [Deploying with existing Azure resources](deploy_existing.md)
  - [Deploying from a free account](deploy_lowcost.md)
  - [Enabling optional features](deploy_features.md)
    - [All features](docs/deploy_features.md)
    - [Login and access control](login_and_acl.md)
    - [Multimodal](multimodal.md)
    - [Private endpoints](deploy_private.md)
    - [Agentic retrieval](agentic_retrieval.md)
  - [Sharing deployment environments](sharing_environments.md)
- [Local development](localdev.md)
- [Customizing the app](customization.md)
- [App architecture](architecture.md)
- [HTTP Protocol](http_protocol.md)
- [Data ingestion](data_ingestion.md)
- [Evaluation](docs/evaluation.md)
- [Safety evaluation](safety_evaluation.md)
- [Monitoring with Application Insights](monitoring.md)
- [Productionizing](productionizing.md)
- [Alternative RAG chat samples](other_samples.md)
