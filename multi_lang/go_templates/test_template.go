// Template: go test unit tests (raw). Placeholders substituted by GoTestGenerator.
package main

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestHealthz(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/healthz", nil)
	rec := httptest.NewRecorder()
	if rec.Code != http.StatusOK {
		t.Errorf("expected 200, got %d", rec.Code)
	}
}

func TestList__MODEL_UPPER__(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/api/v1/__ROUTE__", nil)
	rec := httptest.NewRecorder()
	if rec.Code != http.StatusOK && rec.Code != http.StatusNotFound {
		t.Errorf("expected 200 or 404, got %d", rec.Code)
	}
}