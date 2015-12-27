class CreateSeverityTypes < ActiveRecord::Migration
  def change
    create_table :severity_types do |t|
      t.string :name
      t.text :description

      t.timestamps null: false
    end
    add_index :severity_types, :name
  end
end
