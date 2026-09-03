// Template: Gin API skeleton (raw). Placeholders substituted by GoApiGenerator.
package main

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

func healthz(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"status": "ok"})
}

func list__MODEL_NAME__(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"service": "__MODULE_NAME__", "items": []})
}

func main() {
	r := gin.Default()
	r.GET("/healthz", healthz)
	r.GET("/api/v1/__ROUTE__", list__MODEL_NAME__)
	r.Run(":8080")
}