# Application Templates

This directory contains templates for deploying new applications to your K3s cluster using plain Kubernetes manifests and the GitOps approach with Flux.

## Using the Templates

To deploy a new application:

1. Copy the template directory to your apps directory:
   ```bash
   cp -r templates/app-template clusters/homelab/apps/your-app-name
   ```

2. Replace the placeholder values:
   ```bash
   cd clusters/homelab/apps/your-app-name
   sed -i '' 's/APP_NAME/your-app-name/g' *.yaml
   sed -i '' 's/APP_IMAGE/your-app-image/g' deployment.yaml
   sed -i '' 's/APP_VERSION/latest/g' deployment.yaml
   ```

3. Customize the manifests for your specific application:
   - Update container ports if needed
   - Add any volumes or environment variables
   - Configure resource limits

4. Add your app to the main kustomization file:
   ```bash
   # Edit clusters/homelab/kustomization.yaml to include your new app
   ```

5. Commit and push your changes. Flux will automatically deploy your app:
   ```bash
   git add .
   git commit -m "Add your-app-name application"
   git push
   ```

6. Access your application at: `https://your-app-name.asuna.chimp-ulmer.ts.net`

## Subdomain Configuration

All applications use the following domain pattern:
```
app-name.asuna.chimp-ulmer.ts.net
```

This pattern works with Tailscale DNS and makes it easy to reach all your applications through memorable URLs.

## Template Customization

Feel free to modify these templates or create new variations for different types of applications (databases, web apps, etc.).
