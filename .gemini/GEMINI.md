# Homelab Rules & Best Practices

## 1. Validation is Mandatory
- **Never claim "it works" without proof.**
- Run verification commands before and after changes.
- If a service is "up", curl it to prove it.
- Always read `@project-context/README.md` file at the root of the project.

## 2. Development Workflow
- Always develop and test locally before deploying to the cluster.
- Use `kubectl port-forward` to test services.
- Use `kubectl exec` to test commands.

## 3. GitOps Workflow
- **Git is Truth:** Never `kubectl edit` live resources if you can avoid it.
- **Commit First:** Edit manifest -> Commit -> Apply.

## 4. Node Separation
- **Compute Node (pesubuntu):** GPU workloads (llama.cpp, Whisper) ONLY.
- **Service Node (asuna):** Apps, DBs, and Orchestration ONLY.

