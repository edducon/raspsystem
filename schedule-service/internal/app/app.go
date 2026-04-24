package app

import (
	"context"
	"errors"
	"fmt"
	"io/fs"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"raspyx2/config"
	"raspyx2/internal/handler"
	"raspyx2/internal/repository"
	"raspyx2/internal/service"
	"sort"
	"strings"
	"syscall"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

func Run(cfg *config.Config) {
	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	log := slog.New(slog.NewTextHandler(os.Stdout, nil))
	log.Info("starting schedule-service", slog.String("port", cfg.ServerPort))

	conn, err := InitDBPool(ctx, cfg, log)
	if err != nil {
		log.Error(fmt.Sprintf("error db connection: %v", err))
		return
	}
	defer conn.Close()

	if err := applyMigrations(ctx, conn); err != nil {
		log.Error(fmt.Sprintf("error applying migrations: %v", err))
		return
	}

	repo := repository.NewRepository(conn)
	services := service.NewService(repo)
	handlers := handler.NewHandler(log, services)

	srv := &http.Server{
		Addr:    fmt.Sprintf(":%s", cfg.ServerPort),
		Handler: handlers.InitRoutes(),
	}

	go func() {
		if err := srv.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			log.Error(fmt.Sprintf("error starting server: %v", err))
		}
	}()

	<-ctx.Done()
	stop()

	shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := srv.Shutdown(shutdownCtx); err != nil {
		log.Error("server forced to shutdown", slog.String("error", err.Error()))
	}
}

func InitDBPool(ctx context.Context, cfg *config.Config, log *slog.Logger) (*pgxpool.Pool, error) {
	poolConfig, err := pgxpool.ParseConfig(cfg.DSN())
	if err != nil {
		return nil, err
	}

	var pool *pgxpool.Pool
	for attempt := 1; attempt <= 10; attempt++ {
		select {
		case <-ctx.Done():
			return nil, fmt.Errorf("context canceled while connecting to DB: %w", ctx.Err())
		default:
			pool, err = pgxpool.NewWithConfig(ctx, poolConfig)
			if err == nil {
				err = pool.Ping(ctx)
				if err == nil {
					return pool, nil
				}
				pool.Close()
			}

			log.Info(fmt.Sprintf("failed connect to db, attempt %d", attempt))
			if attempt < 10 {
				time.Sleep(2 * time.Second)
			}
		}
	}

	return nil, fmt.Errorf("failed to connect after %d attempts: %w", 10, err)
}

func applyMigrations(ctx context.Context, pool *pgxpool.Pool) error {
	entries, err := os.ReadDir("migrations")
	if err != nil {
		if errors.Is(err, fs.ErrNotExist) {
			return nil
		}
		return err
	}

	files := make([]string, 0, len(entries))
	for _, entry := range entries {
		if entry.IsDir() || !strings.HasSuffix(entry.Name(), ".up.sql") {
			continue
		}
		files = append(files, entry.Name())
	}
	sort.Strings(files)

	for _, name := range files {
		content, err := os.ReadFile(filepath.Join("migrations", name))
		if err != nil {
			return err
		}
		if strings.TrimSpace(string(content)) == "" {
			continue
		}
		if _, err := pool.Exec(ctx, string(content)); err != nil {
			return fmt.Errorf("%s: %w", name, err)
		}
	}

	return nil
}
