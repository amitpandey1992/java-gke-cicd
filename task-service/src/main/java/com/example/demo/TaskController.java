package com.example.demo;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import jakarta.annotation.PostConstruct;
import java.util.List;

@RestController
@RequestMapping("/api/tasks")
@CrossOrigin(origins = "*") // Allow frontend to communicate directly if needed
public class TaskController {

    @Autowired
    private TaskRepository taskRepository;

    @PostConstruct
    public void initData() {
        if (taskRepository.count() == 0) {
            taskRepository.save(new Task("Set up GKE Cluster", "Provision Autopilot Kubernetes cluster using Terraform", "DONE"));
            taskRepository.save(new Task("Configure Nginx Proxy", "Set up reverse proxy to route frontend & API traffic on port 80", "DONE"));
            taskRepository.save(new Task("Deploy Microservices", "Expose frontend and backend containers via Helm release", "IN_PROGRESS"));
            taskRepository.save(new Task("Enable HTTPS SSL", "Implement Let's Encrypt certificates using GCP Ingress", "TO_DO"));
            taskRepository.save(new Task("Autoscale Pods", "Configure Horizontal Pod Autoscaler (HPA) for heavy load testing", "TO_DO"));
        }
    }

    @GetMapping
    public List<Task> getAllTasks() {
        return taskRepository.findAll();
    }

    @PostMapping
    public Task createTask(@RequestBody Task task) {
        if (task.getStatus() == null) {
            task.setStatus("TO_DO");
        }
        return taskRepository.save(task);
    }

    @PutMapping("/{id}")
    public Task updateTask(@PathVariable Long id, @RequestBody Task taskDetails) {
        Task task = taskRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Task not found with id: " + id));
        
        task.setTitle(taskDetails.getTitle());
        task.setDescription(taskDetails.getDescription());
        task.setStatus(taskDetails.getStatus());
        
        return taskRepository.save(task);
    }

    @DeleteMapping("/{id}")
    public void deleteTask(@PathVariable Long id) {
        Task task = taskRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Task not found with id: " + id));
        taskRepository.delete(task);
    }
}
