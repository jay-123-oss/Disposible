// Template: GORM model (raw). Placeholders substituted by GoModelGenerator.
package main

import "gorm.io/gorm"

type __MODEL_UPPER__ struct {
	ID    uint    `gorm:"primaryKey"`
	Name  string  `gorm:"size:255;not null"`
	Price float64 `gorm:"not null"`
}

func __MODEL_UPPER__Table(db *gorm.DB) *gorm.DB {
	return db.Model(&__MODEL_UPPER__{})
}