#!/bin/zsh

# Скрипт для автоматизации операций по загрузке данных
# Описан в разделе 1 файла documentation/operation_procedure.md
#
# Использование:
#   ./download_data.zsh [PERIOD_DAYS]
#   где PERIOD_DAYS - количество календарных дней для загрузки (по умолчанию: только самый свежий файл)
#
# Примеры:
#   ./download_data.zsh        # Загрузить только самый свежий файл
#   ./download_data.zsh 14     # Загрузить файлы за последние 14 дней

# Функция для логирования
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Функция для проверки успешности выполнения команды
check_success() {
    if [ $? -ne 0 ]; then
        log "Ошибка: $1"
        exit 1
    fi
}

# Получаем период в днях из аргумента (если не указан, используем 0 для загрузки только самого свежего файла)
PERIOD_DAYS=${1:-0}

log "Начало выполнения операций по загрузке данных"
if [ "$PERIOD_DAYS" -gt 0 ]; then
    log "Период загрузки: последние $PERIOD_DAYS календарных дней"
else
    log "Режим загрузки: только самый свежий файл"
fi

# Проверка наличия необходимых файлов и каталогов
if [ ! -d "privatizationplans" ]; then
    log "Ошибка: Каталог privatizationplans не найден"
    exit 1
fi

#if [ ! -d "notice" ]; then
#    log "Ошибка: Каталог notice не найден"
#    exit 1
#fi

# 1. Загрузка метаданных и актуализация основных таблиц

log "1. Загрузка метаданных и актуализация основных таблиц"

log "1.1 Скачивание файла meta.json для планов приватизации"
wget https://torgi.gov.ru/new/opendata/7710568760-privatizationPlans/meta.json -O privatizationplans/meta.json
check_success "Не удалось скачать файл meta.json для планов приватизации"

log "1.2 Загрузка файлов, указанных в meta.json"
python metadownload.py
check_success "Не удалось загрузить файлы, указанные в meta.json"

log "1.3 Перемещение файлов с реестром данных в основные каталоги"
# Для планов приватизации
cd privatizationplans

if [ "$PERIOD_DAYS" -gt 0 ]; then
    # Режим загрузки за период: вычисляем дату начала периода
    cutoff_date=$(date -d "$PERIOD_DAYS days ago" '+%Y%m%d' 2>/dev/null || date -v-${PERIOD_DAYS}d '+%Y%m%d' 2>/dev/null || gdate -d "$PERIOD_DAYS days ago" '+%Y%m%d' 2>/dev/null)
    
    if [ -z "$cutoff_date" ]; then
        log "Ошибка: Не удалось вычислить дату начала периода. Убедитесь, что установлена команда date с поддержкой опции -d или gdate (GNU coreutils)"
        exit 1
    fi
    
    log "Загрузка файлов с датой окончания периода >= $cutoff_date"
    
    # Находим все файлы и фильтруем по дате окончания периода
    files_moved=0
    for file in loaded/data-*.json; do
        if [ ! -f "$file" ]; then
            continue
        fi
        
        # Извлекаем дату окончания периода из имени файла (формат: data-YYYYMMDDTHHMM-YYYYMMDDTHHMM-structure-YYYYMMDD.json)
        filename=$(basename "$file")
        end_date=$(echo "$filename" | sed -n 's/data-[0-9]\{8\}T[0-9]\{4\}-\([0-9]\{8\}\)T[0-9]\{4\}-.*/\1/p')
        
        if [ -n "$end_date" ] && [ "$end_date" -ge "$cutoff_date" ]; then
            log "Перемещение файла: $filename (дата окончания: $end_date)"
            mv "$file" .
            check_success "Не удалось переместить файл $file"
            files_moved=$((files_moved + 1))
        fi
    done
    
    if [ $files_moved -eq 0 ]; then
        log "Предупреждение: Не найдены файлы данных за указанный период в каталоге privatizationplans/loaded"
    else
        log "Перемещено файлов: $files_moved"
    fi
else
    # Режим загрузки только самого свежего файла (обратная совместимость)
    latest_file=$(ls -t loaded/data-*.json 2>/dev/null | head -n1)
    if [ -n "$latest_file" ]; then
        log "Перемещение файла: $(basename "$latest_file")"
        mv "$latest_file" .
        check_success "Не удалось переместить файл $latest_file"
    else
        log "Предупреждение: Не найдены файлы данных в каталоге privatizationplans/loaded"
    fi
fi
cd ..

# Для уведомлений
#cd notice
# Получаем имя файла с самой свежей датой
#latest_file=$(ls -t loaded/data-*.json 2>/dev/null | head -n1)
#if [ -n "$latest_file" ]; then
#    log "Перемещение файла: $latest_file"
#    mv "$latest_file" .
#    check_success "Не удалось переместить файл $latest_file"
#else
#    log "Предупреждение: Не найдены файлы данных в каталоге notice/loaded"
#fi
#cd ..

log "1.4 Загрузка данных в таблицы БД"
#python main.py --noticeupload --privplansupload
uv run main.py --privplansupload
check_success "Не удалось загрузить данные в таблицы БД"

# 2. Обработка мастер-данных
#log "2. Обработка мастер-данных"
#python masterdata.py
#check_success "Не удалось обработать мастер-данные"

# 3. Создание и заполнение основных таблиц
#log "3. Создание и заполнение основных таблиц"
#python main.py --all
#check_success "Не удалось создать и заполнить основные таблицы"

# 4. Экспорт данных в Excel
log "4. Экспорт данных в Excel"
uv run createexcel_privplans.py
check_success "Не удалось экспортировать данные в Excel"

mv privatizationplans/data-*.json privatizationplans/loaded

log "Завершение выполнения операций по загрузке данных"